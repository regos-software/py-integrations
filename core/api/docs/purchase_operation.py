"""REGOS API service for PurchaseOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PurchaseOperationService(RegosAPIService):
    PATH_GET = "PurchaseOperation/Get"
    PATH_ADD = "PurchaseOperation/Add"
    PATH_EDIT = "PurchaseOperation/Edit"
    PATH_DELETE = "PurchaseOperation/Delete"
    PATH_SET_COST_BY_LAST_PURCHASE = "PurchaseOperation/SetCostByLastPurchase"
    PATH_SET_PRICE_BY_PRICE_TYPE = "PurchaseOperation/SetPriceByPriceType"
    PATH_GET_DISCOUNT = "PurchaseOperation/GetDiscount"
    PATH_ADD_DISCOUNT = "PurchaseOperation/AddDiscount"
    PATH_DELETE_DISCOUNT = "PurchaseOperation/DeleteDiscount"
    PATH_MOVE_OPERATIONS = "PurchaseOperation/MoveOperations"
    PATH_COPY_OPERATIONS_FROM_DOC_WHOLE_SALE = "PurchaseOperation/CopyOperationsFromDocWholeSale"
    PATH_COPY_OPERATIONS_FROM_DOC_ORDER_TO_PARTNER = "PurchaseOperation/CopyOperationsFromDocOrderToPartner"
    PATH_COPY_OPERATIONS_FROM_DOC_INVOICE = "PurchaseOperation/CopyOperationsFromDocInvoice"
    REQUEST_MODELS = {
        'add_discount': models.DiscountOperationAdd,
        'copy_operations_from_doc_invoice': models.DocsOperationsCopy,
        'copy_operations_from_doc_order_to_partner': models.DocsOperationsCopy,
        'copy_operations_from_doc_whole_sale': models.DocsOperationsCopy,
        'delete_discount': models.DiscountOperationDelete,
        'get': models.PurchaseOperationGet,
        'get_discount': models.DiscountOperationGet,
        'move_operations': models.DocsOperationsMovement,
        'set_cost_by_last_purchase': models.SetCostByLastPurchase,
        'set_price_by_price_type': models.SetPriceByPriceType_Model,
    }

    async def get(self, req: models.PurchaseOperationGet | dict[str, Any]) -> models.PurchaseOperationRegosOffsettedArrayResult:
        """POST PurchaseOperation/Get."""
        return await self._call(self.PATH_GET, req, models.PurchaseOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.PurchaseOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST PurchaseOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.PurchaseOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST PurchaseOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.PurchaseOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST PurchaseOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_cost_by_last_purchase(self, req: models.SetCostByLastPurchase | dict[str, Any]) -> models.UpdateResult:
        """POST PurchaseOperation/SetCostByLastPurchase."""
        return await self._call(self.PATH_SET_COST_BY_LAST_PURCHASE, req, models.UpdateResult)

    async def set_price_by_price_type(self, req: models.SetPriceByPriceType_Model | dict[str, Any]) -> models.UpdateResult:
        """POST PurchaseOperation/SetPriceByPriceType."""
        return await self._call(self.PATH_SET_PRICE_BY_PRICE_TYPE, req, models.UpdateResult)

    async def get_discount(self, req: models.DiscountOperationGet | dict[str, Any]) -> models.DiscountOperationRegosArrayResult:
        """POST PurchaseOperation/GetDiscount."""
        return await self._call(self.PATH_GET_DISCOUNT, req, models.DiscountOperationRegosArrayResult)

    async def add_discount(self, req: models.DiscountOperationAdd | dict[str, Any]) -> models.UpdateResult:
        """POST PurchaseOperation/AddDiscount."""
        return await self._call(self.PATH_ADD_DISCOUNT, req, models.UpdateResult)

    async def delete_discount(self, req: models.DiscountOperationDelete | dict[str, Any]) -> models.UpdateResult:
        """POST PurchaseOperation/DeleteDiscount."""
        return await self._call(self.PATH_DELETE_DISCOUNT, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST PurchaseOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

    async def copy_operations_from_doc_whole_sale(self, req: models.DocsOperationsCopy | dict[str, Any]) -> models.ObjectRegosObjectResult:
        """POST PurchaseOperation/CopyOperationsFromDocWholeSale."""
        return await self._call(self.PATH_COPY_OPERATIONS_FROM_DOC_WHOLE_SALE, req, models.ObjectRegosObjectResult)

    async def copy_operations_from_doc_order_to_partner(self, req: models.DocsOperationsCopy | dict[str, Any]) -> models.ObjectRegosObjectResult:
        """POST PurchaseOperation/CopyOperationsFromDocOrderToPartner."""
        return await self._call(self.PATH_COPY_OPERATIONS_FROM_DOC_ORDER_TO_PARTNER, req, models.ObjectRegosObjectResult)

    async def copy_operations_from_doc_invoice(self, req: models.DocsOperationsCopy | dict[str, Any]) -> models.ObjectRegosObjectResult:
        """POST PurchaseOperation/CopyOperationsFromDocInvoice."""
        return await self._call(self.PATH_COPY_OPERATIONS_FROM_DOC_INVOICE, req, models.ObjectRegosObjectResult)

__all__ = ['PurchaseOperationService']
