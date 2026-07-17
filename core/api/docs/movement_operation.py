"""REGOS API service for MovementOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class MovementOperationService(RegosAPIService):
    PATH_GET = "MovementOperation/Get"
    PATH_ADD = "MovementOperation/Add"
    PATH_EDIT = "MovementOperation/Edit"
    PATH_DELETE = "MovementOperation/Delete"
    PATH_MOVE_OPERATIONS = "MovementOperation/MoveOperations"
    PATH_SET_PRICE_BY_PRICE_TYPE = "MovementOperation/SetPriceByPriceType"
    REQUEST_MODELS = {
        'get': models.MovementOperationGet,
        'move_operations': models.DocsOperationsMovement,
        'set_price_by_price_type': models.SetPriceByPriceType_Model,
    }

    async def get(self, req: models.MovementOperationGet | dict[str, Any]) -> models.MovementOperationRegosOffsettedArrayResult:
        """POST MovementOperation/Get."""
        return await self._call(self.PATH_GET, req, models.MovementOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.MovementOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST MovementOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.MovementOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST MovementOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.MovementOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST MovementOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST MovementOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

    async def set_price_by_price_type(self, req: models.SetPriceByPriceType_Model | dict[str, Any]) -> models.UpdateResult:
        """POST MovementOperation/SetPriceByPriceType."""
        return await self._call(self.PATH_SET_PRICE_BY_PRICE_TYPE, req, models.UpdateResult)

__all__ = ['MovementOperationService']
