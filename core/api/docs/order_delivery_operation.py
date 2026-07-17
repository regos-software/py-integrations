"""REGOS API service for OrderDeliveryOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class OrderDeliveryOperationService(RegosAPIService):
    PATH_GET = "OrderDeliveryOperation/Get"
    PATH_ADD = "OrderDeliveryOperation/Add"
    PATH_EDIT = "OrderDeliveryOperation/Edit"
    PATH_DELETE = "OrderDeliveryOperation/Delete"
    REQUEST_MODELS = {
        'get': models.OrderDeliveryOperationGet,
    }

    async def get(self, req: models.OrderDeliveryOperationGet | dict[str, Any]) -> models.OrderDeliveryOperationRegosOffsettedArrayResult:
        """POST OrderDeliveryOperation/Get."""
        return await self._call(self.PATH_GET, req, models.OrderDeliveryOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.OrderDeliveryOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderDeliveryOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.OrderDeliveryOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderDeliveryOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.OrderDeliveryOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderDeliveryOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['OrderDeliveryOperationService']
