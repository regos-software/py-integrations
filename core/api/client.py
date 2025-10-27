# core/api/client.py
from __future__ import annotations

import gzip
import json
import time
import uuid
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
    Простой и поддерживаемый клиент REGOS API под конкретный integration_id.

    Делает:
      • рейтлимит по integration_id (RPS + burst)
      • авторизацию через OAuth2 Client Credentials (кэш токена: память + Redis)
      • один повтор при 401 (рефреш токена)
      • аккуратную распаковку gzip-ответов
      • понятное логирование запроса и ответа
    """

    BASE_URL: str = settings.integration_url.rstrip("/")
    RATE_PER_SEC: int = settings.integration_rps
    BURST: int = settings.integration_burst

    # ограничения на превью тел в логах
    REQ_PREVIEW_LIMIT = 64_000   # bytes
    RESP_PREVIEW_LIMIT = 64_000  # chars

    def __init__(self, connected_integration_id: str, timeout: int = 90) -> None:
        self.integration_id = connected_integration_id
        self.client = httpx.AsyncClient(timeout=timeout)

        self._limiter = get_shared_limiter(
            integration_id=self.integration_id,
            rate_per_sec=self.RATE_PER_SEC,
            burst=self.BURST,
        )

        # Важно: можно реюзать self.client в провайдере, чтобы не плодить соединения
        self._oauth = RegosOAuthProvider(http_client=self.client)

        logger.debug(
            "Инициализирован APIClient: base_url=%s, integration_id=%s, rate=%s/s, burst=%s",
            self.BASE_URL, self.integration_id, self.RATE_PER_SEC, self.BURST
        )

    # ------------------------ служебные ------------------------

    @staticmethod
    def _new_trace_id() -> str:
        return uuid.uuid4().hex[:12]

    @staticmethod
    def _mask_bearer(header_val: str) -> str:
        if not header_val.lower().startswith("bearer "):
            return header_val
        token = header_val.split(" ", 1)[1]
        if len(token) <= 10:
            return "Bearer ******"
        return f"Bearer {token[:6]}...{token[-4:]}"

    @staticmethod
    def _prettify_json(text: str) -> str:
        try:
            obj = json.loads(text)
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return text

    @staticmethod
    def _decompress_if_gzip(raw: bytes) -> tuple[bytes, bool]:
        if raw.startswith(b"\x1f\x8b"):
            try:
                return gzip.decompress(raw), True
            except Exception:
                # Если распаковка не удалась — вернём как есть
                return raw, True
        return raw, False

    @staticmethod
    def _serialize_payload(data: Any) -> Any:
        if isinstance(data, BaseModel):
            return data.model_dump(mode="json")
        if isinstance(data, list):
            return [x.model_dump(mode="json") if isinstance(x, BaseModel) else x for x in data]
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

        Правила:
          - сериализация pydantic/словаря/списка
          - рейтлимит
          - Bearer заголовок
          - 401 -> рефреш + один повтор
          - распаковка gzip и json.loads
          - валидация через response_model
        """
        await self._limiter.acquire()

        url = f"{self.BASE_URL}/gateway/out/{self.integration_id}/v1/{method_path.lstrip('/')}"
        trace_id = self._new_trace_id()
        payload = self._serialize_payload(data)

        async def send_once(*, force_refresh: bool) -> httpx.Response:
            headers = await self._auth_headers(trace_id=trace_id, force_refresh=force_refresh)
            req = self.client.build_request("POST", url, json=payload, headers=headers)

            # ---- LOG: кратко и понятно ----
            masked_auth = self._mask_bearer(headers["Authorization"])
            body_bytes = req.content or b""
            body_preview = body_bytes[: self.REQ_PREVIEW_LIMIT].decode("utf-8", errors="replace")
            logger.info("↗️  [trace:%s] POST %s | send=%dB | auth=%s",
                        trace_id, url, len(body_bytes), masked_auth)
            logger.debug("Request headers: %s", {**headers, "Authorization": masked_auth})
            logger.debug("Request body (preview): %s", self._prettify_json(body_preview))

            # ---- Отправка ----
            t0 = time.perf_counter()
            resp = await self.client.send(req)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            # ---- Лог ответа ----
            await resp.aread()  # гарантируем, что resp.content заполнен
            raw = resp.content or b""
            raw_dec, gz = self._decompress_if_gzip(raw)
            text = raw_dec.decode("utf-8", errors="replace")
            text_preview = text[: self.RESP_PREVIEW_LIMIT]

            logger.info("↘️  [trace:%s] %s -> %s in %.1fms | recv=%dB (gzipped=%s)",
                        trace_id, url, resp.status_code, elapsed_ms, len(raw), gz)
            logger.debug("Response headers: %s", dict(resp.headers))
            logger.debug("Response body (preview): %s", self._prettify_json(text_preview))
            return resp

        # Первая попытка
        resp = await send_once(force_refresh=False)

        # Повтор при 401
        if resp.status_code == 401:
            logger.warning("[trace:%s] 401 Unauthorized. Refreshing token and retrying…", trace_id)
            resp = await send_once(force_refresh=True)

        # Ошибки статуса
        resp.raise_for_status()

        # Парс тела (возможно, gzip)
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
        # провайдер использует тот же клиент — отдельного закрытия не требуется

    async def __aenter__(self) -> "APIClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
