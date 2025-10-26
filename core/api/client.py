# core/api/client.py
from __future__ import annotations

import gzip
import json
import time
import shlex
from typing import Any, Type, TypeVar

import httpx
from pydantic import BaseModel

from core.api.rate_limiter import get_shared_limiter
from schemas.api.base import APIBaseResponse
from core.logger import setup_logger
from config.settings import settings

from core.api.regos_oauth import RegosOAuthProvider

logger = setup_logger("api_client")
TResponse = TypeVar("TResponse", bound=BaseModel)


class APIClient:
    """
    Клиент REGOS API под конкретный integration_id.

    Возможности:
      - Рейтлимит: RATE_PER_SEC (rps) + BURST (bucket) общие для всех экземпляров
        с одинаковым integration_id в процессе (через get_shared_limiter).
      - Авторизация: OAuth2 client_credentials с кэшированием токена в Redis.
      - Автоповтор при 401 Unauthorized с принудительным обновлением токена.
      - Поддержка gzip-ответов (ручная распаковка при необходимости).
      - Подробный лог исходящего запроса (URL, заголовки, тело, cURL).
    """

    BASE_URL = settings.integration_url
    RATE_PER_SEC = settings.integration_rps
    BURST = settings.integration_burst

    # ограничитель на размер тела при выводе в лог (на всякий случай)
    _BODY_LOG_LIMIT = 200_000  # 200 KB, чтобы не зашумлять логи

    def __init__(self, connected_integration_id: str, timeout: int = 90):
        self.base_url = self.BASE_URL.rstrip("/")
        self.integration_id = connected_integration_id
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

        # Общий рейт-лимитер по integration_id
        self._limiter = get_shared_limiter(
            self.integration_id,
            self.RATE_PER_SEC,
            self.BURST,
        )

        # OAuth2 (client credentials) провайдер с кэшем в Redis
        self._oauth = RegosOAuthProvider()

        logger.debug(
            "Инициализирован APIClient: base_url=%s, integration_id=%s, rate=%s/s, burst=%s",
            self.base_url,
            self.integration_id,
            self.RATE_PER_SEC,
            self.BURST,
        )

    # ---------- helpers: логирование запроса/ответа ----------
    @staticmethod
    def _mask_secret(val: str, keep_left: int = 6, keep_right: int = 4) -> str:
        if not val:
            return val
        if len(val) <= keep_left + keep_right:
            return "*" * len(val)
        return f"{val[:keep_left]}...{val[-keep_right:]}"

    def _sanitize_headers_for_log(self, headers: dict[str, str]) -> dict[str, str]:
        sanitized: dict[str, str] = {}
        for k, v in headers.items():
            lk = k.lower()
            if lk in ("authorization", "proxy-authorization"):
                # маскируем Bearer токен
                if isinstance(v, str) and v.lower().startswith("bearer "):
                    token = v.split(" ", 1)[1] if " " in v else v
                    sanitized[k] = f"Bearer {self._mask_secret(token)}"
                else:
                    sanitized[k] = self._mask_secret(v)
            elif lk in ("cookie", "set-cookie"):
                sanitized[k] = "<redacted>"
            else:
                sanitized[k] = v
        return sanitized

    def _build_curl(self, method: str, url: str, headers: dict[str, str], body_bytes: bytes | None) -> str:
        # собираем curl со «скобками» вокруг URL и экранированием
        parts = ["curl", "-X", method.upper(), shlex.quote(url)]
        for k, v in headers.items():
            parts += ["-H", shlex.quote(f"{k}: {v}")]
        if body_bytes:
            # показываем данные как есть (json), экранируем одинарные кавычки
            body = body_bytes.decode("utf-8", errors="replace")
            parts += ["--data-raw", shlex.quote(body)]
        return " ".join(parts)

    def _log_request(self, req: httpx.Request):
        # санитизируем заголовки перед логом
        headers_log = self._sanitize_headers_for_log(dict(req.headers))
        body_bytes = req.content or b""
        body_len = len(body_bytes)
        if body_len > self._BODY_LOG_LIMIT:
            body_for_log = body_bytes[: self._BODY_LOG_LIMIT].decode("utf-8", errors="replace") + f"\n... [truncated, total {body_len} bytes]"
        else:
            body_for_log = body_bytes.decode("utf-8", errors="replace")

        curl_cmd = self._build_curl(req.method, str(req.url), headers_log, body_bytes)

        logger.info("POST %s", req.url)
        logger.debug(
            "HTTP REQUEST >>>\n"
            "Method: %s\n"
            "URL: %s\n"
            "Headers: %s\n"
            "Body (%d bytes): %s\n"
            "cURL: %s",
            req.method,
            req.url,
            json.dumps(headers_log, ensure_ascii=False),
            body_len,
            body_for_log,
            curl_cmd,
        )

    def _log_response(self, resp: httpx.Response, elapsed_ms: float, text_preview: str):
        hdrs = self._sanitize_headers_for_log(dict(resp.headers))
        logger.debug(
            "HTTP RESPONSE <<<\n"
            "Status: %s\n"
            "Elapsed: %.1f ms\n"
            "Headers: %s\n"
            "Body preview (first 500 chars): %s",
            resp.status_code,
            elapsed_ms,
            json.dumps(hdrs, ensure_ascii=False),
            text_preview,
        )

    async def _headers(self, force_refresh_token: bool = False) -> dict[str, str]:
        token = await self._oauth.get_access_token(force_refresh=force_refresh_token)
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
        }

    async def post(
        self,
        method_path: str,
        data: Any,
        response_model: Type[TResponse] = APIBaseResponse,
    ) -> TResponse:
        """
        Универсальный POST-запрос:
          - сериализует pydantic-модели/списки/словари,
          - применяет рейтлимит,
          - добавляет Bearer-токен,
          - при 401 обновляет токен и повторяет запрос один раз,
          - распаковывает gzip (если пришёл сырой gzip),
          - валидирует ответ через response_model (pydantic),
          - логирует исходящий запрос (включая cURL) и ответ.
        """
        url = f"{self.base_url}/gateway/out/{self.integration_id}/v1/{method_path.lstrip('/')}"
        await self._limiter.acquire()

        # Сериализация payload
        if isinstance(data, BaseModel):
            payload = data.model_dump(mode="json")
        elif isinstance(data, list):
            payload = [
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in data
            ]
        elif isinstance(data, dict):
            payload = data
        else:
            raise TypeError(f"Unsupported data type for POST: {type(data)}")

        async def _do(force_refresh: bool = False) -> httpx.Response:
            headers = await self._headers(force_refresh_token=force_refresh)
            # build_request позволяет залогировать точный контент
            req = self.client.build_request("POST", url, json=payload, headers=headers)
            # лог исходящего запроса
            self._log_request(req)
            t0 = time.perf_counter()
            resp = await self.client.send(req)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            # краткий превью тела ответа (после .aread() ниже будет полноценный парс)
            try:
                preview_raw = await resp.aread()
                # вернём обратно в буфер для дальнейшей обработки (httpx не умеет «перематывать»),
                # поэтому сохраним в атрибут и используем ниже вместо второго чтения.
                resp._content = preview_raw  # noqa: SLF001 — осознанно, httpx допускает
                preview_text = (
                    gzip.decompress(preview_raw).decode("utf-8", errors="replace")
                    if preview_raw.startswith(b"\x1f\x8b")
                    else preview_raw.decode("utf-8", errors="replace")
                )
            except Exception:
                preview_text = "<unavailable>"
            self._log_response(resp, dt_ms, preview_text[:500])
            return resp

        try:
            resp = await _do(force_refresh=False)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response is not None and e.response.status_code == 401:
                    logger.warning("401 Unauthorized — обновляю токен и повторяю запрос")
                    resp = await _do(force_refresh=True)
                    resp.raise_for_status()
                else:
                    raise

            # Читаем сырые байты (в _do мы уже наполнили resp._content)
            raw = resp.content  # уже содержит bytes после _do()
            if raw.startswith(b"\x1f\x8b"):
                logger.debug("Response is gzip-compressed, decompressing...")
                raw = gzip.decompress(raw)

            text = raw.decode("utf-8", errors="replace")
            logger.debug("Response text (first 500 chars): %s", text[:500])

            parsed = json.loads(text)
            return response_model(**parsed)

        except httpx.RequestError as e:
            logger.error("Ошибка запроса к %s: %s", url, e)
            raise
        except httpx.HTTPStatusError as e:
            body_preview = ""
            try:
                body_preview = e.response.text[:500] if e.response is not None else ""
            except Exception:
                pass
            logger.error(
                "HTTP %s при обращении к %s: %s",
                getattr(e.response, "status_code", "<?>"),
                url,
                body_preview,
            )
            raise
        except Exception as e:
            logger.exception("Непредвиденная ошибка при POST %s: %s", url, e)
            raise

    async def close(self):
        logger.debug("Закрытие httpx.AsyncClient")
        await self.client.aclose()

    # Контекстный менеджер
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
