"""REGOS API service for PaymentType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PaymentTypeService(RegosAPIService):
    PATH_GET = "PaymentType/Get"
    PATH_ADD = "PaymentType/Add"
    PATH_EDIT = "PaymentType/Edit"
    PATH_DELETE = "PaymentType/Delete"
    PATH_GET_IMAGE = "PaymentType/GetImage"
    PATH_ADD_IMAGE = "PaymentType/AddImage"
    PATH_DELETE_IMAGE = "PaymentType/DeleteImage"
    REQUEST_MODELS = {
        'add': models.PaymentTypeAdd,
        'delete': models.PaymentTypeDelete,
        'delete_image': models.Base_ID,
        'edit': models.PaymentTypeEdit,
        'get': models.PaymentTypeGet,
        'get_image': models.PaymentTypeImageGet,
    }

    async def get(self, req: models.PaymentTypeGet | dict[str, Any]) -> models.PaymentTypeArrayRegosObjectResult:
        """POST PaymentType/Get."""
        return await self._call(self.PATH_GET, req, models.PaymentTypeArrayRegosObjectResult)

    async def add(self, req: models.PaymentTypeAdd | dict[str, Any]) -> models.InsertResult:
        """POST PaymentType/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.PaymentTypeEdit | dict[str, Any]) -> models.UpdateResult:
        """POST PaymentType/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.PaymentTypeDelete | dict[str, Any]) -> models.UpdateResult:
        """POST PaymentType/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def get_image(self, req: models.PaymentTypeImageGet | dict[str, Any]) -> models.PaymentTypeImageRegosArrayResult:
        """POST PaymentType/GetImage."""
        return await self._call(self.PATH_GET_IMAGE, req, models.PaymentTypeImageRegosArrayResult)

    async def add_image(self, body: dict[str, Any] | None = None) -> models.UpdateResult:
        """POST PaymentType/AddImage."""
        return await self._call(self.PATH_ADD_IMAGE, body or {}, models.UpdateResult)

    async def delete_image(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST PaymentType/DeleteImage."""
        return await self._call(self.PATH_DELETE_IMAGE, req, models.UpdateResult)

__all__ = ['PaymentTypeService']
