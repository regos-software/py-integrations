"""REGOS API service for OrderToPartnerOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class OrderToPartnerOperationService(RegosAPIService):
    PATH_GET = "OrderToPartnerOperation/Get"
    PATH_ADD = "OrderToPartnerOperation/Add"
    PATH_EDIT = "OrderToPartnerOperation/Edit"
    PATH_DELETE = "OrderToPartnerOperation/Delete"
    PATH_MOVE_OPERATIONS = "OrderToPartnerOperation/MoveOperations"
    REQUEST_MODELS = {
        'get': models.OrderToPartnerOperationGet,
        'move_operations': models.DocsOperationsMovement,
    }

    async def get(self, req: models.OrderToPartnerOperationGet | dict[str, Any]) -> models.OrderToPartnerOperationRegosOffsettedArrayResult:
        """POST OrderToPartnerOperation/Get."""
        return await self._call(self.PATH_GET, req, models.OrderToPartnerOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.OrderToPartnerOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderToPartnerOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.OrderToPartnerOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderToPartnerOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.OrderToPartnerOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderToPartnerOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST OrderToPartnerOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

__all__ = ['OrderToPartnerOperationService']
