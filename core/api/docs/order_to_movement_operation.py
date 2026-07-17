"""REGOS API service for OrderToMovementOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class OrderToMovementOperationService(RegosAPIService):
    PATH_GET = "OrderToMovementOperation/Get"
    PATH_ADD = "OrderToMovementOperation/Add"
    PATH_EDIT = "OrderToMovementOperation/Edit"
    PATH_DELETE = "OrderToMovementOperation/Delete"
    PATH_MOVE_OPERATIONS = "OrderToMovementOperation/MoveOperations"
    REQUEST_MODELS = {
        'get': models.OrderToMovementOperationGet,
        'move_operations': models.DocsOperationsMovement,
    }

    async def get(self, req: models.OrderToMovementOperationGet | dict[str, Any]) -> models.OrderToMovementOperationRegosOffsettedArrayResult:
        """POST OrderToMovementOperation/Get."""
        return await self._call(self.PATH_GET, req, models.OrderToMovementOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.OrderToMovementOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderToMovementOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.OrderToMovementOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderToMovementOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.OrderToMovementOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderToMovementOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST OrderToMovementOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

__all__ = ['OrderToMovementOperationService']
