"""REGOS API service for PromoProgramSetting."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PromoProgramSettingService(RegosAPIService):
    PATH_GET = "PromoProgramSetting/Get"
    PATH_ADD_SINGLE = "PromoProgramSetting/AddSingle"
    PATH_ADD = "PromoProgramSetting/Add"
    PATH_EDIT = "PromoProgramSetting/Edit"
    PATH_DELETE = "PromoProgramSetting/Delete"
    REQUEST_MODELS = {
        'add_single': models.PromoProgramSettingAdd,
        'delete': models.PromoProgramSettingDelete,
        'get': models.PromoProgramSettingGet,
    }

    async def get(self, req: models.PromoProgramSettingGet | dict[str, Any]) -> models.PromoProgramSettingArrayRegosObjectResult:
        """POST PromoProgramSetting/Get."""
        return await self._call(self.PATH_GET, req, models.PromoProgramSettingArrayRegosObjectResult)

    async def add_single(self, req: models.PromoProgramSettingAdd | dict[str, Any]) -> models.InsertResult:
        """POST PromoProgramSetting/AddSingle."""
        return await self._call(self.PATH_ADD_SINGLE, req, models.InsertResult)

    async def add(self, req: list[models.PromoProgramSettingAdd] | list[dict[str, Any]]) -> models.InsertResult:
        """POST PromoProgramSetting/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: list[models.PromoProgramSettingEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST PromoProgramSetting/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.PromoProgramSettingDelete | dict[str, Any]) -> models.UpdateResult:
        """POST PromoProgramSetting/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['PromoProgramSettingService']
