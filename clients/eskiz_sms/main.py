import httpx
import json
import uuid
from typing import Any, Optional  
from core.api.regos_api import RegosAPI
from schemas.integration.sms_integration_base import IntegrationSmsBase
from schemas.api.base import APIBaseResponse
from schemas.api.integrations.connected_integration_setting import ConnectedIntegrationSettingRequest
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

logger = setup_logger("eskiz_sms")


class EskizSmsIntegration(IntegrationSmsBase, ClientBase):
    BASE_URL = "https://notify.eskiz.uz/api"
    ENDPOINTS = {
        "login": f"{BASE_URL}/auth/login",
        "refresh": f"{BASE_URL}/auth/refresh",
        "send_sms": f"{BASE_URL}/message/sms/send",
        "send_batch": f"{BASE_URL}/message/sms/send-batch"
    }
    DEFAULT_TIMEOUT = 15
    BATCH_SIZE = 100
    TOKEN_TTL = 600

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
        if settings.redis_enabled and redis_client:
            cached_settings = await redis_client.get(cache_key)
            if cached_settings:
                logger.debug("Настройки получены из Redis")
                return json.loads(cached_settings)

        logger.debug("Настройки не найдены, загружаем из API")
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
                settings_response = await api.integrations.connected_integration_setting.get(
                    ConnectedIntegrationSettingRequest(
                        integration_key="sms_eskiz"
                    )
                )
        settings_map = {s["key"].lower(): s["value"] for s in settings_response.result}
        if settings.redis_enabled and redis_client:
            await redis_client.setex(cache_key, settings.redis_cache_ttl, json.dumps(settings_map))
        return settings_map

    async def _make_request(self, endpoint: str, data: dict, headers: dict, json: bool = False) -> Any:
        try:
            request_func = self.http_client.post if not endpoint.endswith("refresh") else self.http_client.patch
            response = await request_func(
                endpoint,
                json=data if json else None,
                data=data if not json else None,
                headers=headers
            )
            if response.status_code == 401:
                token = await self.refresh_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    response = await request_func(
                        endpoint,
                        json=data if json else None,
                        data=data if not json else None,
                        headers=headers
                    )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка запроса к {endpoint}: {e}")
            raise

    async def get_token(self, email: str, password: str) -> str:
        token_cache_key = f"clients:token:eskiz:{self.connected_integration_id}"

        if settings.redis_enabled and redis_client:
            cached_token = await redis_client.get(token_cache_key)
            if cached_token:
                logger.debug("Токен найден в Redis")
                return cached_token

        logger.debug("Токен не найден, запрашиваем через API")
        try:
            response = await self._make_request(
                self.ENDPOINTS["login"],
                data={"email": email, "password": password},
                headers={},
                json=False
            )
            token = response.get("data", {}).get("token")
            if not token:
                raise ValueError("Не удалось получить токен авторизации")
            if settings.redis_enabled and redis_client:
                await redis_client.setex(token_cache_key, self.TOKEN_TTL, token)
            return token
        except Exception as e:
            logger.error(f"Ошибка получения токена: {e}")
            raise

    async def refresh_token(self) -> Optional[str]:  
        token_cache_key = f"clients:token:eskiz:{self.connected_integration_id}"
        token = await redis_client.get(token_cache_key)

        if not token:
            logger.warning("Нет токена для обновления")
            return None

        try:
            new_token = await self._make_request(
                self.ENDPOINTS["refresh"],
                data={},
                headers={"Authorization": f"Bearer {token}"},
                json=False
            )
            new_token = new_token.get("data", {}).get("token")
            if new_token and settings.redis_enabled and redis_client:
                await redis_client.setex(token_cache_key, self.TOKEN_TTL, new_token)
                logger.info("Токен успешно обновлён")
            return new_token
        except Exception as e:
            logger.warning(f"Ошибка при обновлении токена: {e}")
            return None

    async def send_messages(self, messages: list[dict]) -> Any:
        logger.info("Начата отправка SMS через ESKIZ")
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id не указан")

        cache_key = f"clients:settings:eskiz:{self.connected_integration_id}"
        try:
            settings_map = await self._get_settings(cache_key)
            email = settings_map.get("eskiz_email")
            password = settings_map.get("eskiz_password")
            sender = settings_map.get("eskiz_nickname", "4546")
            callback_url = settings_map.get("eskiz_callback_url", "")
        except Exception as e:
            return self._error_response(1001, f"Ошибка получения настроек: {e}")

        try:
            token = await self.get_token(email, password)
        except Exception as e:
            return self._error_response(1003, f"Ошибка авторизации: {e}")

        if len(messages) == 1:
            msg = messages[0]
            phone = msg["recipient"].lstrip("+")
            text = msg["message"]
            data = {"mobile_phone": phone, "message": text, "from": sender}
            if callback_url:
                data["callback_url"] = callback_url

            try:
                return await self._make_request(
                    self.ENDPOINTS["send_sms"],
                    data=data,
                    headers={"Authorization": f"Bearer {token}"},
                    json=False
                )
            except Exception as e:
                return self._error_response(1004, f"Ошибка при отправке одиночного SMS: {e}")

        results = []
        for i in range(0, len(messages), self.BATCH_SIZE):
            batch = messages[i:i + self.BATCH_SIZE]
            dispatch_id = str(uuid.uuid4())
            payload = {
                "messages": [
                    {
                        "user_sms_id": f"sms_{i}_{j}",
                        "to": int(msg["recipient"].lstrip("+")),
                        "text": msg["message"]
                    }
                    for j, msg in enumerate(batch)
                ],
                "from": sender,
                "dispatch_id": dispatch_id
            }
            if callback_url:
                payload["callback_url"] = callback_url

            try:
                result = await self._make_request(
                    self.ENDPOINTS["send_batch"],
                    data=payload,
                    headers={"Authorization": f"Bearer {token}"},
                    json=True
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Ошибка при отправке пакета {i}-{i + len(batch)}: {e}")
                results.append({"error": str(e), "batch_index": i})

        return {
            "sent_batches": len(results),
            "details": results
        }
