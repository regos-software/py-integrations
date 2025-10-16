import httpx
import json
from typing import Any
from core.api.regos_api import RegosAPI
from schemas.integration.sms_integration_base import IntegrationSmsBase
from schemas.api.base import APIBaseResponse
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import (
    IntegrationSuccessResponse,
    IntegrationErrorResponse,
    IntegrationErrorModel,
)
from clients.base import ClientBase
from core.api.client import APIClient
from core.logger import setup_logger
from config.settings import settings
from core.redis import redis_client

logger = setup_logger("getsms")


class GetSmsIntegration(IntegrationSmsBase, ClientBase):
    BASE_URL = "http://185.8.212.184/smsgateway/"
    DEFAULT_TIMEOUT = 15
    BATCH_SIZE = 50
    SETTINGS_TTL = settings.redis_cache_ttl
    SETTINGS_KEYS = {
        "login": "getsms_login",
        "password": "getsms_password",
        "nickname": "getsms_nickname",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_client = httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    def _error_response(self, code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    async def _get_settings(self, cache_key: str) -> dict:
        """Получение настроек GETSMS из Redis или API"""
        # 1. Пробуем Redis
        if settings.redis_enabled and redis_client:
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    logger.debug(f"Настройки получены из Redis: {cache_key}")
                    if isinstance(cached_data, (bytes, bytearray)):
                        cached_data = cached_data.decode("utf-8")
                    return json.loads(cached_data)
            except Exception as error:
                logger.warning(f"Ошибка Redis: {error}, загружаем из API")

        # 2. Если нет в кеше — API
        logger.debug(f"Настройки не найдены в кеше, загружаем из API")
        try:
            async with RegosAPI(
                connected_integration_id=self.connected_integration_id
            ) as api:
                settings_response = (
                    await api.integrations.connected_integration_setting.get(
                        ConnectedIntegrationSettingRequest(integration_key="sms_getsms")
                    )
                )

            # settings_response — это список моделей ConnectedIntegrationSetting
            settings_map = {item.key.lower(): item.value for item in settings_response}

            # 3. Сохраняем в Redis
            if settings.redis_enabled and redis_client:
                try:
                    await redis_client.setex(
                        cache_key, self.SETTINGS_TTL, json.dumps(settings_map)
                    )
                except Exception as error:
                    logger.warning(f"Не удалось сохранить настройки в Redis: {error}")

            return settings_map
        except Exception as error:
            logger.error(
                f"Ошибка получения настроек для {self.connected_integration_id}: {error}"
            )
            raise

    async def _make_request(self, data: dict) -> Any:
        try:
            response = await self.http_client.post(
                self.BASE_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            logger.debug(f"Ответ от шлюза: {response.text}")
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка отправки запроса: {e}")
            raise

    async def handle_external(self, data: dict) -> Any:
        """
        Обработка внешних запросов (не от REGOS).
        Пока метод-заглушка, просто логируем данные и возвращаем успех.
        """
        logger.info(f"handle_external вызван с данными: {data}")
        return IntegrationSuccessResponse(result={"status": "ok"})

    async def send_messages(self, messages: list[dict]) -> Any:
        logger.info("Начата отправка SMS через GETSMS")
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id не указан")

        cache_key = f"clients:settings:getsms:{self.connected_integration_id}"
        try:
            settings_map = await self._get_settings(cache_key)
            login = settings_map.get(self.SETTINGS_KEYS["login"])
            password = settings_map.get(self.SETTINGS_KEYS["password"])
            nickname = settings_map.get(self.SETTINGS_KEYS["nickname"])

            if not all([login, password]):
                return self._error_response(
                    1002, "Настройки интеграции не содержат login или password"
                )
        except Exception as e:
            return self._error_response(1001, f"Ошибка при получении настроек: {e}")

        results = []
        for i in range(0, len(messages), self.BATCH_SIZE):
            batch = messages[i : i + self.BATCH_SIZE]
            payload = {
                "login": login,
                "password": password,
                "data": json.dumps(
                    [
                        {"phone": msg["recipient"].lstrip("+"), "text": msg["message"]}
                        for msg in batch
                    ]
                ),
            }
            if nickname:
                payload["nickname"] = nickname

            logger.debug(f"Отправка SMS-пакета ({i}-{i + len(batch)})")
            try:
                result = await self._make_request(payload)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "batch_index": i})

        logger.info(f"Отправка завершена. Обработано пакетов: {len(results)}")
        return {"sent_batches": len(results), "details": results}
