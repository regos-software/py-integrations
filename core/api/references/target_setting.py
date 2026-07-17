"""REGOS API service for TargetSetting."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class TargetSettingService(RegosAPIService):
    PATH_GET = "TargetSetting/Get"
    PATH_ADD_SINGLE = "TargetSetting/AddSingle"
    PATH_ADD = "TargetSetting/Add"
    PATH_DELETE = "TargetSetting/Delete"
    REQUEST_MODELS = {
        'add_single': models.TargetSettingAdd,
        'delete': models.Base_ID,
        'get': models.TargetSettingGet,
    }

    async def get(self, req: models.TargetSettingGet | dict[str, Any]) -> models.TargetSettingRegosArrayResult:
        """POST TargetSetting/Get."""
        return await self._call(self.PATH_GET, req, models.TargetSettingRegosArrayResult)

    async def add_single(self, req: models.TargetSettingAdd | dict[str, Any]) -> models.InsertResult:
        """POST TargetSetting/AddSingle."""
        return await self._call(self.PATH_ADD_SINGLE, req, models.InsertResult)

    async def add(self, req: list[models.TargetSettingAdd] | list[dict[str, Any]]) -> models.InsertResult:
        """POST TargetSetting/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST TargetSetting/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['TargetSettingService']
