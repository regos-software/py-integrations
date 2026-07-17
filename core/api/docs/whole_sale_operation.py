"""REGOS API service for WholeSaleOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class WholeSaleOperationService(RegosAPIService):
    PATH_GET = "WholeSaleOperation/Get"
    PATH_ADD = "WholeSaleOperation/Add"
    PATH_EDIT = "WholeSaleOperation/Edit"
    PATH_DELETE = "WholeSaleOperation/Delete"
    PATH_GET_DISCOUNT = "WholeSaleOperation/GetDiscount"
    PATH_ADD_DISCOUNT = "WholeSaleOperation/AddDiscount"
    PATH_DELETE_DISCOUNT = "WholeSaleOperation/DeleteDiscount"
    PATH_MOVE_OPERATIONS = "WholeSaleOperation/MoveOperations"
    PATH_COPY_OPERATIONS_FROM_DOC_PURCHASE = "WholeSaleOperation/CopyOperationsFromDocPurchase"
    PATH_COPY_OPERATIONS_FROM_DOC_ORDER_FROM_PARTNER = "WholeSaleOperation/CopyOperationsFromDocOrderFromPartner"
    PATH_SET_PRICE_BY_PRICE_TYPE = "WholeSaleOperation/SetPriceByPriceType"
    REQUEST_MODELS = {
        'add_discount': models.DiscountOperationAdd,
        'copy_operations_from_doc_order_from_partner': models.DocsOperationsCopy,
        'copy_operations_from_doc_purchase': models.DocsOperationsCopy,
        'delete_discount': models.DiscountOperationDelete,
        'get': models.WholeSaleOperationGet,
        'get_discount': models.DiscountOperationGet,
        'move_operations': models.DocsOperationsMovement,
        'set_price_by_price_type': models.SetPriceByPriceType_Model,
    }

    async def get(self, req: models.WholeSaleOperationGet | dict[str, Any]) -> models.WholeSaleOperationRegosOffsettedArrayResult:
        """POST WholeSaleOperation/Get."""
        return await self._call(self.PATH_GET, req, models.WholeSaleOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.WholeSaleOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST WholeSaleOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.WholeSaleOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST WholeSaleOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.WholeSaleOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST WholeSaleOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def get_discount(self, req: models.DiscountOperationGet | dict[str, Any]) -> models.DiscountOperationRegosArrayResult:
        """POST WholeSaleOperation/GetDiscount."""
        return await self._call(self.PATH_GET_DISCOUNT, req, models.DiscountOperationRegosArrayResult)

    async def add_discount(self, req: models.DiscountOperationAdd | dict[str, Any]) -> models.UpdateResult:
        """POST WholeSaleOperation/AddDiscount."""
        return await self._call(self.PATH_ADD_DISCOUNT, req, models.UpdateResult)

    async def delete_discount(self, req: models.DiscountOperationDelete | dict[str, Any]) -> models.UpdateResult:
        """POST WholeSaleOperation/DeleteDiscount."""
        return await self._call(self.PATH_DELETE_DISCOUNT, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST WholeSaleOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

    async def copy_operations_from_doc_purchase(self, req: models.DocsOperationsCopy | dict[str, Any]) -> models.UpdateResult:
        """POST WholeSaleOperation/CopyOperationsFromDocPurchase."""
        return await self._call(self.PATH_COPY_OPERATIONS_FROM_DOC_PURCHASE, req, models.UpdateResult)

    async def copy_operations_from_doc_order_from_partner(self, req: models.DocsOperationsCopy | dict[str, Any]) -> models.UpdateResult:
        """POST WholeSaleOperation/CopyOperationsFromDocOrderFromPartner."""
        return await self._call(self.PATH_COPY_OPERATIONS_FROM_DOC_ORDER_FROM_PARTNER, req, models.UpdateResult)

    async def set_price_by_price_type(self, req: models.SetPriceByPriceType_Model | dict[str, Any]) -> models.UpdateResult:
        """POST WholeSaleOperation/SetPriceByPriceType."""
        return await self._call(self.PATH_SET_PRICE_BY_PRICE_TYPE, req, models.UpdateResult)

__all__ = ['WholeSaleOperationService']
