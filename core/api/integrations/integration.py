"""REGOS API service for Integration."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class IntegrationService(RegosAPIService):
    PATH_GET = "Integration/Get"
    PATH_CONNECT = "Integration/Connect"
    PATH_ADD = "Integration/Add"
    PATH_EDIT = "Integration/Edit"
    PATH_DELETE = "Integration/Delete"
    REQUEST_MODELS = {
        'add': models.IntegrationLocalAdd,
        'connect': models.IntegrationConnect,
        'delete': models.IntegrationLocalDelete,
        'edit': models.IntegrationLocalEdit,
        'get': models.IntegrationUnConnectedGet,
    }

    async def get(self, req: models.IntegrationUnConnectedGet | dict[str, Any]) -> models.IntegrationUnConnectedRegosOffsettedArrayResult:
        """POST Integration/Get."""
        return await self._call(self.PATH_GET, req, models.IntegrationUnConnectedRegosOffsettedArrayResult)

    async def connect(self, req: models.IntegrationConnect | dict[str, Any]) -> models.SingleObjectResult:
        """POST Integration/Connect."""
        return await self._call(self.PATH_CONNECT, req, models.SingleObjectResult)

    async def add(self, req: models.IntegrationLocalAdd | dict[str, Any]) -> models.SingleObjectResult:
        """POST Integration/Add."""
        return await self._call(self.PATH_ADD, req, models.SingleObjectResult)

    async def edit(self, req: models.IntegrationLocalEdit | dict[str, Any]) -> models.SingleObjectResult:
        """POST Integration/Edit."""
        return await self._call(self.PATH_EDIT, req, models.SingleObjectResult)

    async def delete(self, req: models.IntegrationLocalDelete | dict[str, Any]) -> models.SingleObjectResult:
        """POST Integration/Delete."""
        return await self._call(self.PATH_DELETE, req, models.SingleObjectResult)

__all__ = ['IntegrationService']
