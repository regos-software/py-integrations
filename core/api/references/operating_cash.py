"""REGOS API service for OperatingCash."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class OperatingCashService(RegosAPIService):
    PATH_GET = "OperatingCash/Get"
    PATH_ADD = "OperatingCash/Add"
    PATH_EDIT = "OperatingCash/Edit"
    PATH_DELETE = "OperatingCash/Delete"
    PATH_ACCEPT = "OperatingCash/Accept"
    PATH_DISCARD = "OperatingCash/Discard"
    PATH_GET_SETTINGS = "OperatingCash/GetSettings"
    PATH_EDIT_SETTINGS = "OperatingCash/EditSettings"
    PATH_GET_CHEQUE_TEMPLATE = "OperatingCash/GetChequeTemplate"
    PATH_EDIT_CHEQUE_TEMPLATE = "OperatingCash/EditChequeTemplate"
    PATH_GET_IMAGE = "OperatingCash/GetImage"
    PATH_ADD_IMAGE = "OperatingCash/AddImage"
    PATH_DELETE_IMAGE = "OperatingCash/DeleteImage"
    REQUEST_MODELS = {
        'accept': models.OperatingCashAccept,
        'add': models.OperatingCashAdd,
        'delete': models.OperatingCashDelete,
        'delete_image': models.OperatingCashImageDelete,
        'discard': models.OperatingCashDiscard,
        'edit': models.OperatingCashEdit,
        'edit_cheque_template': models.OperatingCashChequeTemplateEdit,
        'get': models.OperatingCashGet,
        'get_cheque_template': models.OperatingCashChequeTemplateGet,
        'get_image': models.OperatingCashImageGet,
        'get_settings': models.OperatingCash_SettingGet,
    }

    async def get(self, req: models.OperatingCashGet | dict[str, Any]) -> models.OperatingCashRegosOffsettedArrayResult:
        """POST OperatingCash/Get."""
        return await self._call(self.PATH_GET, req, models.OperatingCashRegosOffsettedArrayResult)

    async def add(self, req: models.OperatingCashAdd | dict[str, Any]) -> models.InsertResult:
        """POST OperatingCash/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.OperatingCashEdit | dict[str, Any]) -> models.UpdateResult:
        """POST OperatingCash/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.OperatingCashDelete | dict[str, Any]) -> models.UpdateResult:
        """POST OperatingCash/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def accept(self, req: models.OperatingCashAccept | dict[str, Any]) -> models.ObjectRegosObjectResult:
        """POST OperatingCash/Accept."""
        return await self._call(self.PATH_ACCEPT, req, models.ObjectRegosObjectResult)

    async def discard(self, req: models.OperatingCashDiscard | dict[str, Any]) -> models.ObjectRegosObjectResult:
        """POST OperatingCash/Discard."""
        return await self._call(self.PATH_DISCARD, req, models.ObjectRegosObjectResult)

    async def get_settings(self, req: models.OperatingCash_SettingGet | dict[str, Any]) -> models.OperatingCash_SettingArrayRegosObjectResult:
        """POST OperatingCash/GetSettings."""
        return await self._call(self.PATH_GET_SETTINGS, req, models.OperatingCash_SettingArrayRegosObjectResult)

    async def edit_settings(self, req: list[models.OperatingCash_SettingEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OperatingCash/EditSettings."""
        return await self._call(self.PATH_EDIT_SETTINGS, req, models.UpdateResult)

    async def get_cheque_template(self, req: models.OperatingCashChequeTemplateGet | dict[str, Any]) -> models.OperatingCashChequeTemplateRegosOffsettedArrayResult:
        """POST OperatingCash/GetChequeTemplate."""
        return await self._call(self.PATH_GET_CHEQUE_TEMPLATE, req, models.OperatingCashChequeTemplateRegosOffsettedArrayResult)

    async def edit_cheque_template(self, req: models.OperatingCashChequeTemplateEdit | dict[str, Any]) -> models.UpdateResult:
        """POST OperatingCash/EditChequeTemplate."""
        return await self._call(self.PATH_EDIT_CHEQUE_TEMPLATE, req, models.UpdateResult)

    async def get_image(self, req: models.OperatingCashImageGet | dict[str, Any]) -> models.OperatingCashImageRegosArrayResult:
        """POST OperatingCash/GetImage."""
        return await self._call(self.PATH_GET_IMAGE, req, models.OperatingCashImageRegosArrayResult)

    async def add_image(self, body: dict[str, Any] | None = None) -> models.UpdateResult:
        """POST OperatingCash/AddImage."""
        return await self._call(self.PATH_ADD_IMAGE, body or {}, models.UpdateResult)

    async def delete_image(self, req: models.OperatingCashImageDelete | dict[str, Any]) -> models.UpdateResult:
        """POST OperatingCash/DeleteImage."""
        return await self._call(self.PATH_DELETE_IMAGE, req, models.UpdateResult)

__all__ = ['OperatingCashService']
