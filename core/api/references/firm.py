"""REGOS API service for Firm."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class FirmService(RegosAPIService):
    PATH_GET = "Firm/Get"
    PATH_ADD = "Firm/Add"
    PATH_EDIT = "Firm/Edit"
    PATH_DELETE_MARK = "Firm/DeleteMark"
    PATH_DELETE = "Firm/Delete"
    PATH_DELETE_CONFIRM = "Firm/DeleteConfirm"
    PATH_GET_IMAGE = "Firm/GetImage"
    PATH_ADD_IMAGE = "Firm/AddImage"
    PATH_DELETE_IMAGE = "Firm/DeleteImage"
    PATH_GET_SETTINGS = "Firm/GetSettings"
    PATH_EDIT_SETTINGS = "Firm/EditSettings"
    REQUEST_MODELS = {
        'add': models.FirmAdd,
        'delete': models.FirmDelete,
        'delete_confirm': models.FirmDeleteConfirm,
        'delete_image': models.FirmImageDelete,
        'delete_mark': models.FirmDeleteMark,
        'edit': models.FirmEdit,
        'get': models.FirmGet,
        'get_image': models.FirmImageGet,
        'get_settings': models.Firm_SettingGet,
    }

    async def get(self, req: models.FirmGet | dict[str, Any]) -> models.FirmRegosOffsettedArrayResult:
        """POST Firm/Get."""
        return await self._call(self.PATH_GET, req, models.FirmRegosOffsettedArrayResult)

    async def add(self, req: models.FirmAdd | dict[str, Any]) -> models.InsertResult:
        """POST Firm/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.FirmEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Firm/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.FirmDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST Firm/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.FirmDelete | dict[str, Any]) -> models.ApiResult:
        """POST Firm/Delete."""
        return await self._call(self.PATH_DELETE, req, models.ApiResult)

    async def delete_confirm(self, req: models.FirmDeleteConfirm | dict[str, Any]) -> models.ApiResult:
        """POST Firm/DeleteConfirm."""
        return await self._call(self.PATH_DELETE_CONFIRM, req, models.ApiResult)

    async def get_image(self, req: models.FirmImageGet | dict[str, Any]) -> models.FirmImageRegosArrayResult:
        """POST Firm/GetImage."""
        return await self._call(self.PATH_GET_IMAGE, req, models.FirmImageRegosArrayResult)

    async def add_image(self, body: dict[str, Any] | None = None) -> models.UpdateResult:
        """POST Firm/AddImage."""
        return await self._call(self.PATH_ADD_IMAGE, body or {}, models.UpdateResult)

    async def delete_image(self, req: models.FirmImageDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Firm/DeleteImage."""
        return await self._call(self.PATH_DELETE_IMAGE, req, models.UpdateResult)

    async def get_settings(self, req: models.Firm_SettingGet | dict[str, Any]) -> models.FirmSettingArrayRegosObjectResult:
        """POST Firm/GetSettings."""
        return await self._call(self.PATH_GET_SETTINGS, req, models.FirmSettingArrayRegosObjectResult)

    async def edit_settings(self, req: list[models.Firm_SettingEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST Firm/EditSettings."""
        return await self._call(self.PATH_EDIT_SETTINGS, req, models.UpdateResult)

__all__ = ['FirmService']
