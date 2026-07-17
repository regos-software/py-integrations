from abc import ABC
from typing import Any, Optional
from schemas.integration.integration_base import IntegrationBase
from schemas.integration.base import (
    IntegrationSuccessResponse,
    IntegrationErrorResponse,
    IntegrationErrorModel,
)


class IntegrationEmailBase(IntegrationBase, ABC):
    """
    Базовый класс для EMAIL-интеграций с REGOS.
    Содержит заглушки для базовых методов и обязательно требует реализации send_messages.
    """

    async def connect(self, *args, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub connect"})

    async def disconnect(self, *args, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub disconnect"})

    async def reconnect(self, *args, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub reconnect"})

    async def update_settings(self, *args, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub update_settings"})

    async def handle_webhook(self, data: Optional[dict] = None, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub handle_webhook"})

    async def handle_external(self, data: Optional[dict] = None, **kwargs) -> Any:
        return IntegrationSuccessResponse(result={"status": "stub handle_external"})

    async def send_messages(self, messages: list[dict]) -> Any:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(
                error=9999, description="send_messages not implemented"
            )
        )
