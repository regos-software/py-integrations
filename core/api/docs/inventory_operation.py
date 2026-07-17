"""REGOS API service for InventoryOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class InventoryOperationService(RegosAPIService):
    PATH_GET = "InventoryOperation/Get"
    PATH_ADD = "InventoryOperation/Add"
    PATH_ADD_BULK = "InventoryOperation/AddBulk"
    PATH_EDIT = "InventoryOperation/Edit"
    PATH_DELETE = "InventoryOperation/Delete"
    PATH_MOVE_OPERATIONS = "InventoryOperation/MoveOperations"
    PATH_SET_PRICE_BY_PRICE_TYPE = "InventoryOperation/SetPriceByPriceType"
    REQUEST_MODELS = {
        'add_bulk': models.InventoryOperationAddBulk,
        'get': models.InventoryOperationGet,
        'move_operations': models.DocsOperationsMovement,
        'set_price_by_price_type': models.SetPriceByPriceType_Model,
    }

    async def get(self, req: models.InventoryOperationGet | dict[str, Any]) -> models.InventoryOperationRegosOffsettedArrayResult:
        """POST InventoryOperation/Get."""
        return await self._call(self.PATH_GET, req, models.InventoryOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.InventoryOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST InventoryOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def add_bulk(self, req: models.InventoryOperationAddBulk | dict[str, Any]) -> models.UpdateResult:
        """POST InventoryOperation/AddBulk."""
        return await self._call(self.PATH_ADD_BULK, req, models.UpdateResult)

    async def edit(self, req: list[models.InventoryOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST InventoryOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.InventoryOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST InventoryOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST InventoryOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

    async def set_price_by_price_type(self, req: models.SetPriceByPriceType_Model | dict[str, Any]) -> models.UpdateResult:
        """POST InventoryOperation/SetPriceByPriceType."""
        return await self._call(self.PATH_SET_PRICE_BY_PRICE_TYPE, req, models.UpdateResult)

__all__ = ['InventoryOperationService']
