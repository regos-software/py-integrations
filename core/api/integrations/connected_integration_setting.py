"""REGOS API service for ConnectedIntegrationSetting."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ConnectedIntegrationSettingService(RegosAPIService):
    PATH_GET = "ConnectedIntegrationSetting/Get"
    PATH_EDIT = "ConnectedIntegrationSetting/Edit"
    REQUEST_MODELS = {
        'get': models.ConnectedIntegrationSettingGet,
    }

    async def get(self, req: models.ConnectedIntegrationSettingGet | dict[str, Any]) -> models.ConnectedIntegrationSettingRegosArrayResult:
        """POST ConnectedIntegrationSetting/Get."""
        return await self._call(self.PATH_GET, req, models.ConnectedIntegrationSettingRegosArrayResult)

    async def edit(self, req: list[models.ConnectedIntegrationSettingEdit] | list[dict[str, Any]]) -> models.SingleObjectResult:
        """POST ConnectedIntegrationSetting/Edit."""
        return await self._call(self.PATH_EDIT, req, models.SingleObjectResult)

__all__ = ['ConnectedIntegrationSettingService']
