"""REGOS API service for OrderFromPartnerOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class OrderFromPartnerOperationService(RegosAPIService):
    PATH_GET = "OrderFromPartnerOperation/Get"
    PATH_ADD = "OrderFromPartnerOperation/Add"
    PATH_EDIT = "OrderFromPartnerOperation/Edit"
    PATH_DELETE = "OrderFromPartnerOperation/Delete"
    PATH_MOVE_OPERATIONS = "OrderFromPartnerOperation/MoveOperations"
    PATH_GET_DISCOUNT = "OrderFromPartnerOperation/GetDiscount"
    PATH_ADD_DISCOUNT = "OrderFromPartnerOperation/AddDiscount"
    PATH_DELETE_DISCOUNT = "OrderFromPartnerOperation/DeleteDiscount"
    REQUEST_MODELS = {
        'add_discount': models.DiscountOperationAdd,
        'delete_discount': models.DiscountOperationDelete,
        'get': models.OrderFromPartnerOperationGet,
        'get_discount': models.DiscountOperationGet,
        'move_operations': models.DocsOperationsMovement,
    }

    async def get(self, req: models.OrderFromPartnerOperationGet | dict[str, Any]) -> models.OrderFromPartnerOperationRegosOffsettedArrayResult:
        """POST OrderFromPartnerOperation/Get."""
        return await self._call(self.PATH_GET, req, models.OrderFromPartnerOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.OrderFromPartnerOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderFromPartnerOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.OrderFromPartnerOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderFromPartnerOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.OrderFromPartnerOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST OrderFromPartnerOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST OrderFromPartnerOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

    async def get_discount(self, req: models.DiscountOperationGet | dict[str, Any]) -> models.DiscountOperationRegosArrayResult:
        """POST OrderFromPartnerOperation/GetDiscount."""
        return await self._call(self.PATH_GET_DISCOUNT, req, models.DiscountOperationRegosArrayResult)

    async def add_discount(self, req: models.DiscountOperationAdd | dict[str, Any]) -> models.UpdateResult:
        """POST OrderFromPartnerOperation/AddDiscount."""
        return await self._call(self.PATH_ADD_DISCOUNT, req, models.UpdateResult)

    async def delete_discount(self, req: models.DiscountOperationDelete | dict[str, Any]) -> models.UpdateResult:
        """POST OrderFromPartnerOperation/DeleteDiscount."""
        return await self._call(self.PATH_DELETE_DISCOUNT, req, models.UpdateResult)

__all__ = ['OrderFromPartnerOperationService']
