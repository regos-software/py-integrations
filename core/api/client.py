# core/api/client.py
from __future__ import annotations

import gzip
import json
import time
import uuid
import logging
from typing import Any, Dict, Type, TypeVar

import httpx
from pydantic import BaseModel

from config.settings import settings
from core.api.rate_limiter import get_shared_limiter
from core.api.regos_oauth import RegosOAuthProvider
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse

logger = setup_logger("api_client")
TResponse = TypeVar("TResponse", bound=BaseModel)


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

    REQ_PREVIEW_LIMIT = 2_048    # bytes
    RESP_PREVIEW_LIMIT = 2_048   # chars

    def __init__(self, connected_integration_id: str, timeout: int = 90) -> None:
        self.integration_id = connected_integration_id
        self.client = httpx.AsyncClient(timeout=timeout)

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

    async def _auth_headers(self, *, trace_id: str, force_refresh: bool = False) -> Dict[str, str]:
        token = await self._oauth.get_access_token(force_refresh=force_refresh)
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "X-Request-Id": trace_id,
        }

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
        await self._limiter.acquire()

        url = f"{self.BASE_URL}/gateway/out/{self.integration_id}/v1/{method_path.lstrip('/')}"
        trace_id = self._new_trace_id()
        payload = self._serialize_payload(data)

        async def send_once(*, force_refresh: bool) -> httpx.Response:
            headers = await self._auth_headers(trace_id=trace_id, force_refresh=force_refresh)
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
            t0 = time.perf_counter()
            resp = await self.client.send(req)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            # читаем тело
            await resp.aread()
            raw = resp.content or b""
            raw_dec, gz = self._decompress_if_gzip(raw)
            text = raw_dec.decode("utf-8", errors="replace")

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
        resp = await send_once(force_refresh=False)

        # Повтор при 401
        if resp.status_code == 401:
            logger.warning("[trace:%s] 401 Unauthorized. Refreshing token and retrying…", trace_id)
            resp = await send_once(force_refresh=True)

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

    # ---------------------- lifecycle -------------------------

    async def close(self) -> None:
        logger.debug("Закрытие httpx.AsyncClient")
        await self.client.aclose()

    async def __aenter__(self) -> "APIClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
