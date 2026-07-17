"""REGOS API service for DeliveryCourier."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DeliveryCourierService(RegosAPIService):
    PATH_GET = "DeliveryCourier/Get"
    PATH_ADD = "DeliveryCourier/Add"
    PATH_EDIT = "DeliveryCourier/Edit"
    PATH_DELETE = "DeliveryCourier/Delete"
    REQUEST_MODELS = {
        'add': models.DeliveryCourierAdd,
        'delete': models.DeliveryCourierDelete,
        'edit': models.DeliveryCourierEdit,
        'get': models.DeliveryCourierGet,
    }

    async def get(self, req: models.DeliveryCourierGet | dict[str, Any]) -> models.DeliveryCourierRegosOffsettedArrayResult:
        """POST DeliveryCourier/Get."""
        return await self._call(self.PATH_GET, req, models.DeliveryCourierRegosOffsettedArrayResult)

    async def add(self, req: models.DeliveryCourierAdd | dict[str, Any]) -> models.InsertResult:
        """POST DeliveryCourier/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DeliveryCourierEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DeliveryCourier/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.DeliveryCourierDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DeliveryCourier/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DeliveryCourierService']
