"""REGOS API service for DeliveryFrom."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DeliveryFromService(RegosAPIService):
    PATH_GET = "DeliveryFrom/Get"
    PATH_ADD = "DeliveryFrom/Add"
    PATH_EDIT = "DeliveryFrom/Edit"
    PATH_DELETE = "DeliveryFrom/Delete"
    REQUEST_MODELS = {
        'add': models.DeliveryFromAdd,
        'delete': models.DeliveryFromDelete,
        'edit': models.DeliveryFromEdit,
        'get': models.DeliveryFromGet,
    }

    async def get(self, req: models.DeliveryFromGet | dict[str, Any]) -> models.DeliveryFromRegosOffsettedArrayResult:
        """POST DeliveryFrom/Get."""
        return await self._call(self.PATH_GET, req, models.DeliveryFromRegosOffsettedArrayResult)

    async def add(self, req: models.DeliveryFromAdd | dict[str, Any]) -> models.InsertResult:
        """POST DeliveryFrom/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DeliveryFromEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DeliveryFrom/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.DeliveryFromDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DeliveryFrom/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DeliveryFromService']
