"""REGOS API service for DeliveryType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DeliveryTypeService(RegosAPIService):
    PATH_GET = "DeliveryType/Get"
    PATH_ADD = "DeliveryType/Add"
    PATH_EDIT = "DeliveryType/Edit"
    PATH_DELETE = "DeliveryType/Delete"
    REQUEST_MODELS = {
        'add': models.DeliveryTypeAdd,
        'delete': models.DeliveryTypeDelete,
        'edit': models.DeliveryTypeEdit,
        'get': models.DeliveryTypeGet,
    }

    async def get(self, req: models.DeliveryTypeGet | dict[str, Any]) -> models.DeliveryTypeRegosOffsettedArrayResult:
        """POST DeliveryType/Get."""
        return await self._call(self.PATH_GET, req, models.DeliveryTypeRegosOffsettedArrayResult)

    async def add(self, req: models.DeliveryTypeAdd | dict[str, Any]) -> models.InsertResult:
        """POST DeliveryType/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DeliveryTypeEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DeliveryType/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.DeliveryTypeDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DeliveryType/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DeliveryTypeService']
