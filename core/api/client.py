import httpx
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel

from schemas.api.base import APIBaseResponse
from core.logger import setup_logger
from config.settings import settings

logger = setup_logger("api_client")
TResponse = TypeVar("TResponse", bound=BaseModel)


class APIClient:
    """
    Универсальный клиент REGOS API для работы с конкретной интеграцией по её ID.
    """

    BASE_URL = settings.integration_url  

    def __init__(
        self,
        connected_integration_id: str,
        timeout: int = 90
    ):
        self.base_url = self.BASE_URL
        self.integration_id = connected_integration_id
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

        logger.debug(f"Инициализирован APIClient: base_url={self.base_url}, integration_id={self.integration_id}")

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        logger.debug(f"Сформированы заголовки: {headers}")
        return headers

    async def post(
        self,
        method_path: str,
        data: Any,
        response_model: Type[TResponse] = APIBaseResponse
    ) -> TResponse:
        """
        Универсальный POST-запрос к методам интеграции.
        """
        url = f"{self.base_url}/gateway/out/{self.integration_id}/v1/{method_path}"

        #  Исправление: поддерживаем list, dict и BaseModel
        if isinstance(data, BaseModel):
            payload = data.model_dump()
        elif isinstance(data, (list, dict)):
            payload = data
        else:
            raise TypeError(f"Unsupported data type for POST: {type(data)}")

        logger.info(f"POST {url}")
        logger.debug(f"Payload: {payload}")

        try:
            resp = await self.client.post(url, json=payload, headers=self._headers())
            logger.debug(f"Response status: {resp.status_code}")
            logger.debug(f"Response body: {resp.text}")
            resp.raise_for_status()
            return response_model(**resp.json())
        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса к {url}: {str(e)}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка HTTP {e.response.status_code} при обращении к {url}: {e.response.text}")
            raise
        except Exception as e:
            logger.exception(f"Непредвиденная ошибка при POST {url}: {str(e)}")
            raise


    async def close(self):
        logger.debug("Закрытие httpx.AsyncClient")
        await self.client.aclose()  
