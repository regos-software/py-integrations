from abc import ABC
from typing import Any
from schemas.integration.integration_base import IntegrationBase
from schemas.integration.base import IntegrationSuccessResponse, IntegrationErrorResponse, IntegrationErrorModel


class IntegrationSmsBase(IntegrationBase, ABC):
    """
    Базовый класс для SMS-интеграций с REGOS.
    Добавляет метод отправки сообщений + дефолтные заглушки для остальных методов.
    """

    async def connect(self, *args, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub connect"})

    async def disconnect(self, *args, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub disconnect"})

    async def reconnect(self, *args, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub reconnect"})

    async def update_settings(self, *args, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub update_settings"})

    async def handle_webhook(self, data: dict | None = None, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub handle_webhook"})

    async def handle_external(self, data: dict | None = None, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub handle_external"})

    async def send_messages(self, messages: list[dict]) -> Any:
        """
        Метод отправки сообщений должен быть обязательно переопределён
        в конкретной SMS-интеграции.
        """
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=9999, description="send_messages not implemented")
        )
