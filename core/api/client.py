# core/api/client.py
from __future__ import annotations

import gzip
import json
from typing import Any, Type, TypeVar

import httpx
from pydantic import BaseModel

from core.api.rate_limiter import get_shared_limiter
from schemas.api.base import APIBaseResponse
from core.logger import setup_logger
from config.settings import settings

from core.api.regos_oauth import RedisClientCredentialsProvider

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

    Пример:
        async with APIClient("your_integration_id") as api:
            resp = await api.post("orders/list", {"page": 1, "size": 20})
            print(resp)
    """

    BASE_URL = settings.integration_url
    RATE_PER_SEC = settings.integration_rps
    BURST = settings.integration_burst

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
        self._oauth = RedisClientCredentialsProvider()

        logger.debug(
            "Инициализирован APIClient: base_url=%s, integration_id=%s, rate=%s/s, burst=%s",
            self.base_url,
            self.integration_id,
            self.RATE_PER_SEC,
            self.BURST,
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
          - валидирует ответ через response_model (pydantic).
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

        logger.info("POST %s", url)
        logger.debug("Payload: %s", payload)

        async def _do(force_refresh: bool = False) -> httpx.Response:
            headers = await self._headers(force_refresh_token=force_refresh)
            return await self.client.post(url, json=payload, headers=headers)

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

            # Читаем сырые байты (минуя авто-декодинг) и, при необходимости, разgzip-ваем вручную
            raw = await resp.aread()
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
