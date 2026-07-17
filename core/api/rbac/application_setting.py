"""REGOS API service for ApplicationSetting."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ApplicationSettingService(RegosAPIService):
    PATH_GET_VALUES = "ApplicationSetting/GetValues"
    PATH_EDIT_VALUES = "ApplicationSetting/EditValues"
    PATH_ADD = "ApplicationSetting/Add"
    PATH_GET = "ApplicationSetting/Get"
    PATH_DELETE = "ApplicationSetting/Delete"
    REQUEST_MODELS = {
        'add': models.ApplicationSettingAdd,
        'delete': models.ApplicationSettingDelete,
        'get': models.ApplicationSettingGet,
        'get_values': models.ApplicationSettingValuesGet,
    }

    async def get_values(self, req: models.ApplicationSettingValuesGet | dict[str, Any]) -> models.ApplicationSettingValueArrayRegosObjectResult:
        """POST ApplicationSetting/GetValues."""
        return await self._call(self.PATH_GET_VALUES, req, models.ApplicationSettingValueArrayRegosObjectResult)

    async def edit_values(self, req: list[models.ApplicationSettingValuesEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST ApplicationSetting/EditValues."""
        return await self._call(self.PATH_EDIT_VALUES, req, models.UpdateResult)

    async def add(self, req: models.ApplicationSettingAdd | dict[str, Any]) -> models.InsertResult:
        """POST ApplicationSetting/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def get(self, req: models.ApplicationSettingGet | dict[str, Any]) -> models.ApplicationSettingArrayRegosObjectResult:
        """POST ApplicationSetting/Get."""
        return await self._call(self.PATH_GET, req, models.ApplicationSettingArrayRegosObjectResult)

    async def delete(self, req: models.ApplicationSettingDelete | dict[str, Any]) -> models.UpdateResult:
        """POST ApplicationSetting/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['ApplicationSettingService']
