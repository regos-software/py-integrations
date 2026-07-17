"""REGOS API service for FirmGroup."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class FirmGroupService(RegosAPIService):
    PATH_GET = "FirmGroup/Get"
    PATH_ADD = "FirmGroup/Add"
    PATH_EDIT = "FirmGroup/Edit"
    PATH_DELETE = "FirmGroup/Delete"
    REQUEST_MODELS = {
        'add': models.FirmGroupAdd,
        'delete': models.FirmGroupDelete,
        'edit': models.FirmGroupEdit,
        'get': models.FirmGroupGet,
    }

    async def get(self, req: models.FirmGroupGet | dict[str, Any]) -> models.FirmGroupArrayRegosObjectResult:
        """POST FirmGroup/Get."""
        return await self._call(self.PATH_GET, req, models.FirmGroupArrayRegosObjectResult)

    async def add(self, req: models.FirmGroupAdd | dict[str, Any]) -> models.InsertResult:
        """POST FirmGroup/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.FirmGroupEdit | dict[str, Any]) -> models.UpdateResult:
        """POST FirmGroup/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.FirmGroupDelete | dict[str, Any]) -> models.UpdateResult:
        """POST FirmGroup/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['FirmGroupService']
