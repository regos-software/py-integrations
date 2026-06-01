# core/api/client.py
from __future__ import annotations

import asyncio
import datetime
import email.utils
import gzip
import json
import random
import time
import uuid
import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel

from config.settings import settings
from core.api.rate_limiter import get_shared_limiter
from core.api.regos_oauth import RegosOAuthProvider
from core.logger import setup_logger
from core.redis import redis_is_enabled, redis_ops
from schemas.api.base import APIBaseResponse

logger = setup_logger("api_client")
TResponse = TypeVar("TResponse", bound=BaseModel)

_RATE_LIMIT_COOLDOWNS: Dict[str, float] = {}
_RATE_LIMIT_COOLDOWN_LOCK = asyncio.Lock()


class APIClient:
    """
    Лёгкий клиент REGOS API с минималистичным логированием.

    INFO:
      → перед отправкой: метод, URL, объём отправки
      ← после ответа: статус, время, объём приёма, gzip yes/no

    DEBUG:
      - Request headers + короткий превью тела запроса (до 2 KB)
      - Response headers + короткий превью тела ответа ТОЛЬКО при статусе >= 400
    """

    BASE_URL: str = settings.integration_url.rstrip("/")
    RATE_PER_SEC: int = settings.integration_rps
    BURST: int = settings.integration_burst
    RATE_LIMIT_RETRY_ATTEMPTS: int = max(
        int(settings.integration_429_retry_attempts or 0),
        1,
    )
    RATE_LIMIT_BASE_DELAY_SEC: float = max(
        float(settings.integration_429_base_delay_sec or 0),
        0.1,
    )
    RATE_LIMIT_MAX_DELAY_SEC: float = max(
        float(settings.integration_429_max_delay_sec or 0),
        1.0,
    )
    RATE_LIMIT_COOLDOWN_TTL_SEC: int = max(
        int(settings.integration_429_cooldown_ttl_sec or 0),
        30,
    )

    REQ_PREVIEW_LIMIT = 2_048    # bytes
    RESP_PREVIEW_LIMIT = 2_048   # chars

    def __init__(self, connected_integration_id: str, timeout: int = 90) -> None:
        self.integration_id = connected_integration_id
        self._timeout = timeout
        self.client = self._build_http_client()

        self._limiter = get_shared_limiter(
            self.integration_id,
            self.RATE_PER_SEC,
            self.BURST,
        )

        # реюзаем общий httpx-клиент в провайдере токена
        self._oauth = RegosOAuthProvider(http_client=self.client)

        logger.debug(
            "Инициализирован APIClient: base_url=%s, integration_id=%s, rate=%s/s, burst=%s",
            self.BASE_URL, self.integration_id, self.RATE_PER_SEC, self.BURST
        )

    # ------------------------ helpers ------------------------

    @staticmethod
    def _new_trace_id() -> str:
        return uuid.uuid4().hex[:12]

    @staticmethod
    def _mask_bearer(header_val: str) -> str:
        if not isinstance(header_val, str) or not header_val.lower().startswith("bearer "):
            return header_val
        token = header_val.split(" ", 1)[1]
        if len(token) <= 10:
            return "Bearer ******"
        return f"Bearer {token[:6]}...{token[-4:]}"

    @staticmethod
    def _decompress_if_gzip(raw: bytes) -> tuple[bytes, bool]:
        if raw.startswith(b"\x1f\x8b"):
            try:
                return gzip.decompress(raw), True
            except Exception:
                return raw, True
        return raw, False

    @staticmethod
    def _fmt_size(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n}{unit}"
            n //= 1024
        return f"{n}GB"

    def _build_http_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self._timeout)

    async def _reset_http_client(self, reason: Optional[Exception] = None) -> None:
        old_client = self.client
        self.client = self._build_http_client()
        self._oauth = RegosOAuthProvider(http_client=self.client)
        try:
            await old_client.aclose()
        except Exception:
            pass
        if reason is not None:
            logger.warning(
                "Reset API HTTP client after transport error: integration_id=%s error=%s",
                self.integration_id,
                reason,
            )

    @staticmethod
    def _serialize_payload(data: Any) -> Any:
        if isinstance(data, BaseModel):
            return data.model_dump(mode="json", exclude_none=True)
        if isinstance(data, list):
            return [
                x.model_dump(mode="json", exclude_none=True) if isinstance(x, BaseModel) else x
                for x in data
            ]
        if isinstance(data, dict):
            return data
        raise TypeError(f"Unsupported data type for POST: {type(data)}")

    async def _auth_headers(
        self,
        *,
        trace_id: str,
        force_refresh: bool = False,
        with_json_content_type: bool = True,
    ) -> Dict[str, str]:
        token = await self._oauth.get_access_token(force_refresh=force_refresh)
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "X-Request-Id": trace_id,
        }
        if with_json_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    def _rate_limit_cooldown_key(self) -> str:
        return f"api:regos:429:{self.integration_id}"

    @staticmethod
    def _parse_retry_after(value: Optional[str]) -> Optional[float]:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            seconds = float(text)
            return max(seconds, 0.0)
        except ValueError:
            pass
        try:
            retry_at = email.utils.parsedate_to_datetime(text)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=datetime.timezone.utc)
            delay = retry_at.timestamp() - time.time()
            return max(delay, 0.0)
        except Exception:
            return None

    def _rate_limit_delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
        if retry_after is not None:
            return min(max(retry_after, 0.1), self.RATE_LIMIT_MAX_DELAY_SEC)
        exponential = self.RATE_LIMIT_BASE_DELAY_SEC * (2 ** max(attempt, 0))
        jitter = random.uniform(0, min(exponential * 0.25, 1.0))
        return min(exponential + jitter, self.RATE_LIMIT_MAX_DELAY_SEC)

    async def _wait_for_rate_limit_cooldown(self, *, trace_id: str, url: str) -> None:
        key = self._rate_limit_cooldown_key()
        now = time.time()
        async with _RATE_LIMIT_COOLDOWN_LOCK:
            cooldown_until = float(_RATE_LIMIT_COOLDOWNS.get(key) or 0)
            if cooldown_until <= now:
                _RATE_LIMIT_COOLDOWNS.pop(key, None)
                cooldown_until = 0

        if redis_is_enabled():
            try:
                raw = await redis_ops.get(key)
                if raw:
                    cooldown_until = max(cooldown_until, float(raw))
            except Exception as error:
                logger.warning(
                    "[trace:%s] Failed to read REGOS 429 cooldown: integration_id=%s error=%s",
                    trace_id,
                    self.integration_id,
                    error,
                )

        delay = cooldown_until - time.time()
        if delay <= 0:
            return
        logger.warning(
            "[trace:%s] Waiting %.2fs for REGOS 429 cooldown: integration_id=%s url=%s",
            trace_id,
            delay,
            self.integration_id,
            url,
        )
        await asyncio.sleep(delay)

    async def _mark_rate_limit_cooldown(
        self,
        *,
        trace_id: str,
        url: str,
        delay_seconds: float,
    ) -> None:
        delay = min(
            max(float(delay_seconds or 0), 0.1),
            self.RATE_LIMIT_MAX_DELAY_SEC,
        )
        cooldown_until = time.time() + delay
        key = self._rate_limit_cooldown_key()
        async with _RATE_LIMIT_COOLDOWN_LOCK:
            _RATE_LIMIT_COOLDOWNS[key] = max(
                float(_RATE_LIMIT_COOLDOWNS.get(key) or 0),
                cooldown_until,
            )

        if redis_is_enabled():
            try:
                ttl = max(
                    int(delay) + 5,
                    min(self.RATE_LIMIT_COOLDOWN_TTL_SEC, 30),
                )
                await redis_ops.set(key, str(cooldown_until), ex=ttl)
            except Exception as error:
                logger.warning(
                    "[trace:%s] Failed to write REGOS 429 cooldown: integration_id=%s error=%s",
                    trace_id,
                    self.integration_id,
                    error,
                )

        logger.warning(
            "[trace:%s] REGOS 429 cooldown set for %.2fs: integration_id=%s url=%s",
            trace_id,
            delay,
            self.integration_id,
            url,
        )

    async def _send_with_rate_limit_retry(
        self,
        *,
        trace_id: str,
        url: str,
        send_once: Callable[[], Awaitable[httpx.Response]],
    ) -> httpx.Response:
        last_response: Optional[httpx.Response] = None
        for attempt in range(self.RATE_LIMIT_RETRY_ATTEMPTS):
            await self._wait_for_rate_limit_cooldown(trace_id=trace_id, url=url)
            await self._limiter.acquire()
            response = await send_once()
            last_response = response
            if response.status_code != 429:
                return response

            delay = self._rate_limit_delay(response, attempt)
            await self._mark_rate_limit_cooldown(
                trace_id=trace_id,
                url=url,
                delay_seconds=delay,
            )
            if attempt >= self.RATE_LIMIT_RETRY_ATTEMPTS - 1:
                return response
            await asyncio.sleep(delay)

        if last_response is None:
            raise RuntimeError("REGOS request was not sent")
        return last_response

    # ------------------------- POST ---------------------------

    async def post(
        self,
        method_path: str,
        data: Any,
        response_model: Type[TResponse] = APIBaseResponse,
    ) -> TResponse:
        """
        POST {BASE_URL}/gateway/out/{integration_id}/v1/{method_path}
        Сериализация -> рейтлимит -> Bearer -> запрос -> (401→рефреш) -> JSON -> валидация.
        """
        url = f"{self.BASE_URL}/gateway/out/{self.integration_id}/v1/{method_path.lstrip('/')}"
        trace_id = self._new_trace_id()
        payload = self._serialize_payload(data)

        async def send_once(*, force_refresh: bool) -> httpx.Response:
            headers = await self._auth_headers(
                trace_id=trace_id,
                force_refresh=force_refresh,
                with_json_content_type=True,
            )
            req = self.client.build_request("POST", url, json=payload, headers=headers)

            # INFO: кратко
            body_bytes = req.content or b""
            logger.info("→ [trace:%s] POST %s | send=%s",
                        trace_id, url, self._fmt_size(len(body_bytes)))

            # DEBUG: заголовки + короткий превью тела запроса
            if logger.isEnabledFor(logging.DEBUG):
                masked_headers = dict(headers)
                masked_headers["Authorization"] = self._mask_bearer(headers.get("Authorization", ""))
                preview = body_bytes[: self.REQ_PREVIEW_LIMIT].decode("utf-8", errors="replace")
                logger.debug("Request headers: %s", masked_headers)
                logger.debug("Request body (%dB, preview): %s", len(body_bytes), preview)

            # отправляем
            try:
                t0 = time.perf_counter()
                resp = await self.client.send(req)
                elapsed_ms = (time.perf_counter() - t0) * 1000.0

                # читаем тело
                await resp.aread()
                raw = resp.content or b""
                raw_dec, gz = self._decompress_if_gzip(raw)
                text = raw_dec.decode("utf-8", errors="replace")
            except httpx.RequestError as error:
                await self._reset_http_client(reason=error)
                raise

            # INFO: кратко
            logger.info("← [trace:%s] %s -> %s in %.1fms | recv=%s | gz=%s",
                        trace_id, url, resp.status_code, elapsed_ms, self._fmt_size(len(raw)), "yes" if gz else "no")

            # DEBUG: заголовки + тело ТОЛЬКО при ошибках
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response headers: %s", dict(resp.headers))
                if resp.status_code >= 400:
                    logger.debug("Response body (preview): %s", text[: self.RESP_PREVIEW_LIMIT])

            # положим обратно уже декодированный текст для последующего парсинга
            resp._decoded_text = text  # внутреннее поле для нашего использования
            return resp

        # Первая попытка
        resp = await self._send_with_rate_limit_retry(
            trace_id=trace_id,
            url=url,
            send_once=lambda: send_once(force_refresh=False),
        )

        # Повтор при 401
        if resp.status_code == 401:
            logger.warning("[trace:%s] 401 Unauthorized. Refreshing token and retrying...", trace_id)
            resp = await self._send_with_rate_limit_retry(
                trace_id=trace_id,
                url=url,
                send_once=lambda: send_once(force_refresh=True),
            )
            if resp.status_code == 401:
                logger.warning(
                    "[trace:%s] 401 persists after token refresh. Resetting transport and retrying once more...",
                    trace_id,
                )
                await self._reset_http_client()
                resp = await self._send_with_rate_limit_retry(
                    trace_id=trace_id,
                    url=url,
                    send_once=lambda: send_once(force_refresh=True),
                )

        # Ошибки статуса
        resp.raise_for_status()

        # Парс JSON
        text = getattr(resp, "_decoded_text", None)
        if text is None:
            raw = resp.content or b""
            raw_dec, _ = self._decompress_if_gzip(raw)
            text = raw_dec.decode("utf-8", errors="replace")

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("[trace:%s] Некорректный JSON в ответе: %s", trace_id, e)
            raise

        return response_model(**parsed)

    async def post_multipart(
        self,
        method_path: str,
        data: Dict[str, Any],
        files: Dict[str, tuple[str, bytes] | tuple[str, bytes, str]],
        response_model: Type[TResponse] = APIBaseResponse,
    ) -> TResponse:
        """
        POST multipart/form-data
        {BASE_URL}/gateway/out/{integration_id}/v1/{method_path}
        """
        url = f"{self.BASE_URL}/gateway/out/{self.integration_id}/v1/{method_path.lstrip('/')}"
        trace_id = self._new_trace_id()
        form_data = {k: str(v) for k, v in data.items() if v is not None}

        async def send_once(*, force_refresh: bool) -> httpx.Response:
            headers = await self._auth_headers(
                trace_id=trace_id,
                force_refresh=force_refresh,
                with_json_content_type=False,
            )
            req = self.client.build_request(
                "POST",
                url,
                data=form_data,
                files=files,
                headers=headers,
            )

            body_bytes = req.content or b""
            logger.info(
                "→ [trace:%s] POST %s (multipart) | send=%s",
                trace_id,
                url,
                self._fmt_size(len(body_bytes)),
            )

            if logger.isEnabledFor(logging.DEBUG):
                masked_headers = dict(headers)
                masked_headers["Authorization"] = self._mask_bearer(
                    headers.get("Authorization", "")
                )
                files_meta: Dict[str, Dict[str, Any]] = {}
                for key, file_tuple in files.items():
                    filename = file_tuple[0]
                    content = file_tuple[1]
                    content_type = file_tuple[2] if len(file_tuple) > 2 else None
                    files_meta[key] = {
                        "filename": filename,
                        "size": len(content) if isinstance(content, (bytes, bytearray)) else None,
                        "content_type": content_type,
                    }
                logger.debug("Request headers: %s", masked_headers)
                logger.debug("Multipart fields: %s", form_data)
                logger.debug("Multipart files: %s", files_meta)

            try:
                t0 = time.perf_counter()
                resp = await self.client.send(req)
                elapsed_ms = (time.perf_counter() - t0) * 1000.0

                await resp.aread()
                raw = resp.content or b""
                raw_dec, gz = self._decompress_if_gzip(raw)
                text = raw_dec.decode("utf-8", errors="replace")
            except httpx.RequestError as error:
                await self._reset_http_client(reason=error)
                raise

            logger.info(
                "← [trace:%s] %s -> %s in %.1fms | recv=%s | gz=%s",
                trace_id,
                url,
                resp.status_code,
                elapsed_ms,
                self._fmt_size(len(raw)),
                "yes" if gz else "no",
            )

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response headers: %s", dict(resp.headers))
                if resp.status_code >= 400:
                    logger.debug("Response body (preview): %s", text[: self.RESP_PREVIEW_LIMIT])

            resp._decoded_text = text
            return resp

        resp = await self._send_with_rate_limit_retry(
            trace_id=trace_id,
            url=url,
            send_once=lambda: send_once(force_refresh=False),
        )
        if resp.status_code == 401:
            logger.warning(
                "[trace:%s] 401 Unauthorized. Refreshing token and retrying...", trace_id
            )
            resp = await self._send_with_rate_limit_retry(
                trace_id=trace_id,
                url=url,
                send_once=lambda: send_once(force_refresh=True),
            )
            if resp.status_code == 401:
                logger.warning(
                    "[trace:%s] 401 persists after token refresh. Resetting transport and retrying once more...",
                    trace_id,
                )
                await self._reset_http_client()
                resp = await self._send_with_rate_limit_retry(
                    trace_id=trace_id,
                    url=url,
                    send_once=lambda: send_once(force_refresh=True),
                )

        resp.raise_for_status()

        text = getattr(resp, "_decoded_text", None)
        if text is None:
            raw = resp.content or b""
            raw_dec, _ = self._decompress_if_gzip(raw)
            text = raw_dec.decode("utf-8", errors="replace")

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("[trace:%s] Некорректный JSON в ответе: %s", trace_id, e)
            raise

        return response_model(**parsed)

    # ---------------------- lifecycle -------------------------

    async def close(self) -> None:
        logger.debug("Закрытие httpx.AsyncClient")
        await self.client.aclose()

    async def __aenter__(self) -> "APIClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
