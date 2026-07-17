"""REGOS API service for ReturnsToPartnerOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ReturnsToPartnerOperationService(RegosAPIService):
    PATH_GET = "ReturnsToPartnerOperation/Get"
    PATH_ADD = "ReturnsToPartnerOperation/Add"
    PATH_EDIT = "ReturnsToPartnerOperation/Edit"
    PATH_DELETE = "ReturnsToPartnerOperation/Delete"
    PATH_SET_COST_BY_LAST_PURCHASE = "ReturnsToPartnerOperation/SetCostByLastPurchase"
    PATH_GET_DISCOUNT = "ReturnsToPartnerOperation/GetDiscount"
    PATH_ADD_DISCOUNT = "ReturnsToPartnerOperation/AddDiscount"
    PATH_DELETE_DISCOUNT = "ReturnsToPartnerOperation/DeleteDiscount"
    PATH_MOVE_OPERATIONS = "ReturnsToPartnerOperation/MoveOperations"
    REQUEST_MODELS = {
        'add_discount': models.DiscountOperationAdd,
        'delete_discount': models.DiscountOperationDelete,
        'get': models.ReturnsToPartnerOperationGet,
        'get_discount': models.DiscountOperationGet,
        'move_operations': models.DocsOperationsMovement,
        'set_cost_by_last_purchase': models.SetCostByLastReturnToPartner,
    }

    async def get(self, req: models.ReturnsToPartnerOperationGet | dict[str, Any]) -> models.ReturnsToPartnerOperationRegosOffsettedArrayResult:
        """POST ReturnsToPartnerOperation/Get."""
        return await self._call(self.PATH_GET, req, models.ReturnsToPartnerOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.ReturnsToPartnerOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST ReturnsToPartnerOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.ReturnsToPartnerOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST ReturnsToPartnerOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.ReturnsToPartnerOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST ReturnsToPartnerOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_cost_by_last_purchase(self, req: models.SetCostByLastReturnToPartner | dict[str, Any]) -> models.UpdateResult:
        """POST ReturnsToPartnerOperation/SetCostByLastPurchase."""
        return await self._call(self.PATH_SET_COST_BY_LAST_PURCHASE, req, models.UpdateResult)

    async def get_discount(self, req: models.DiscountOperationGet | dict[str, Any]) -> models.DiscountOperationRegosArrayResult:
        """POST ReturnsToPartnerOperation/GetDiscount."""
        return await self._call(self.PATH_GET_DISCOUNT, req, models.DiscountOperationRegosArrayResult)

    async def add_discount(self, req: models.DiscountOperationAdd | dict[str, Any]) -> models.UpdateResult:
        """POST ReturnsToPartnerOperation/AddDiscount."""
        return await self._call(self.PATH_ADD_DISCOUNT, req, models.UpdateResult)

    async def delete_discount(self, req: models.DiscountOperationDelete | dict[str, Any]) -> models.UpdateResult:
        """POST ReturnsToPartnerOperation/DeleteDiscount."""
        return await self._call(self.PATH_DELETE_DISCOUNT, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST ReturnsToPartnerOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

__all__ = ['ReturnsToPartnerOperationService']
