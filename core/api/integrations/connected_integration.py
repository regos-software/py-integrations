"""REGOS API service for ConnectedIntegration."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ConnectedIntegrationService(RegosAPIService):
    PATH_GET = "ConnectedIntegration/Get"
    PATH_EDIT = "ConnectedIntegration/Edit"
    PATH_CHECK = "ConnectedIntegration/Check"
    PATH_RECONNECT = "ConnectedIntegration/Reconnect"
    PATH_DISCONNECT = "ConnectedIntegration/Disconnect"
    PATH_GET_WEBHOOK_INFO = "ConnectedIntegration/GetWebhookInfo"
    REQUEST_MODELS = {
        'check': models.ConnectedIntegrationID,
        'disconnect': models.IntegrationDisconnect,
        'edit': models.ConnectedIntegrationEdit,
        'get': models.IntegrationConnectedGet,
        'get_webhook_info': models.ConnectedIntegrationWebhookInfoGet,
        'reconnect': models.IntegrationReconnect,
    }

    async def get(self, req: models.IntegrationConnectedGet | dict[str, Any]) -> models.IntegrationConnectedRegosArrayResult:
        """POST ConnectedIntegration/Get."""
        return await self._call(self.PATH_GET, req, models.IntegrationConnectedRegosArrayResult)

    async def edit(self, req: models.ConnectedIntegrationEdit | dict[str, Any]) -> models.SingleObjectResult:
        """POST ConnectedIntegration/Edit."""
        return await self._call(self.PATH_EDIT, req, models.SingleObjectResult)

    async def check(self, req: models.ConnectedIntegrationID | dict[str, Any]) -> models.BooleanRegosObjectResult:
        """POST ConnectedIntegration/Check."""
        return await self._call(self.PATH_CHECK, req, models.BooleanRegosObjectResult)

    async def reconnect(self, req: models.IntegrationReconnect | dict[str, Any]) -> models.SingleObjectResult:
        """POST ConnectedIntegration/Reconnect."""
        return await self._call(self.PATH_RECONNECT, req, models.SingleObjectResult)

    async def disconnect(self, req: models.IntegrationDisconnect | dict[str, Any]) -> models.SingleObjectResult:
        """POST ConnectedIntegration/Disconnect."""
        return await self._call(self.PATH_DISCONNECT, req, models.SingleObjectResult)

    async def get_webhook_info(self, req: models.ConnectedIntegrationWebhookInfoGet | dict[str, Any]) -> models.WebHookStatusResponseRegosObjectResult:
        """POST ConnectedIntegration/GetWebhookInfo."""
        return await self._call(self.PATH_GET_WEBHOOK_INFO, req, models.WebHookStatusResponseRegosObjectResult)

__all__ = ['ConnectedIntegrationService']
