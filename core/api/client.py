import gzip
import json
from typing import Any, Type, TypeVar

import httpx
from pydantic import BaseModel

from core.api.rate_limiter import get_shared_limiter
from schemas.api.base import APIBaseResponse
from core.logger import setup_logger
from config.settings import settings


logger = setup_logger("api_client")
TResponse = TypeVar("TResponse", bound=BaseModel)


class APIClient:
    """
    Универсальный клиент REGOS API под конкретный integration_id.
    Соблюдает рейтлимит: 2 req/s + ведро на 50 (общий для всех экземпляров
    с одинаковым integration_id внутри процесса).
    """

    BASE_URL = settings.integration_url
    RATE_PER_SEC = settings.integration_rps  # requests per second
    BURST = settings.integration_burst  # bucket size

    def __init__(self, connected_integration_id: str, timeout: int = 90):
        self.base_url = self.BASE_URL
        self.integration_id = connected_integration_id
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

        self._limiter = get_shared_limiter(
            self.integration_id, self.RATE_PER_SEC, self.BURST
        )

        logger.debug(
            f"Инициализирован APIClient: base_url={self.base_url}, "
            f"integration_id={self.integration_id}, rate={self.RATE_PER_SEC}/s, burst={self.BURST}"
        )

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        logger.debug(f"Сформированы заголовки: {headers}")
        return headers

    async def post(
        self,
        method_path: str,
        data: Any,
        response_model: Type[TResponse] = APIBaseResponse,
    ) -> TResponse:
        """
        Универсальный POST-запрос к методам интеграции.
        Обрабатывает gzip-сжатые и обычные ответы.
        Учитывает рейтлимит по integration_id.
        """
        url = f"{self.base_url}/gateway/out/{self.integration_id}/v1/{method_path}"

        # ---- РЕЙТЛИМИТ: дождаться токен перед каждым запросом ----
        await self._limiter.acquire()

        # сериализация
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

        logger.info(f"POST {url}")
        logger.debug(f"Payload: {payload}")

        try:
            resp = await self.client.post(url, json=payload, headers=self._headers())

            # статус проверяем до чтения тела
            resp.raise_for_status()

            # читаем байты тела
            raw = await resp.aread()

            # если gzip — распаковываем, иначе используем как есть
            if raw.startswith(b"\x1f\x8b"):
                logger.debug("Response is gzip-compressed, decompressing...")
                raw = gzip.decompress(raw)

            text = raw.decode("utf-8", errors="replace")
            logger.debug(f"Response text (first 500 chars): {text[:500]}")

            data = json.loads(text)
            return response_model(**data)

        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса к {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP {e.response.status_code} при обращении к {url}: {e.response.text}"
            )
            raise
        except Exception as e:
            logger.exception(f"Непредвиденная ошибка при POST {url}: {e}")
            raise

    async def close(self):
        logger.debug("Закрытие httpx.AsyncClient")
        await self.client.aclose()

    # Удобный контекстный менеджер
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
