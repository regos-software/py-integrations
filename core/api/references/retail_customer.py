"""REGOS API service for RetailCustomer."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RetailCustomerService(RegosAPIService):
    PATH_GET = "RetailCustomer/Get"
    PATH_ADD = "RetailCustomer/Add"
    PATH_EDIT = "RetailCustomer/Edit"
    PATH_DELETE_MARK = "RetailCustomer/DeleteMark"
    PATH_DELETE = "RetailCustomer/Delete"
    PATH_GET_FAVORITE_PURCHASES = "RetailCustomer/GetFavoritePurchases"
    PATH_GET_AVG_CHEQUE_AMOUNT = "RetailCustomer/GetAvgChequeAmount"
    PATH_GET_LAST_PURCHASE_DATE = "RetailCustomer/GetLastPurchaseDate"
    PATH_GET_CHEQUE_COUNT = "RetailCustomer/GetChequeCount"
    PATH_GET_PURCHASE_INFO = "RetailCustomer/GetPurchaseInfo"
    PATH_GET_DEBTS = "RetailCustomer/GetDebts"
    PATH_GET_DEBTS_PAYMENT_HISTORY = "RetailCustomer/GetDebtsPaymentHistory"
    PATH_ADD_DEBT = "RetailCustomer/AddDebt"
    PATH_ADD_DEBT_PAYMENT = "RetailCustomer/AddDebtPayment"
    REQUEST_MODELS = {
        'add': models.RetailCustomerAdd,
        'add_debt': models.RetailCustomerDebtAdd,
        'add_debt_payment': models.RetailCustomerDebtPaymentAdd,
        'delete': models.RetailCustomerDelete,
        'delete_mark': models.RetailCustomerDeleteMark,
        'edit': models.RetailCustomerEdit,
        'get': models.RetailCustomerGet,
        'get_avg_cheque_amount': models.RetailCustomerPurchaseRequest,
        'get_cheque_count': models.RetailCustomerPurchaseRequest,
        'get_debts': models.RetailCustomerDebtRecordGet,
        'get_debts_payment_history': models.RetailCustomerDebtPaymentsdGet,
        'get_favorite_purchases': models.RetailCustomerPurchaseRequest,
        'get_last_purchase_date': models.RetailCustomerPurchaseRequest,
        'get_purchase_info': models.RetailCustomerPurchaseInfoRequest,
    }

    async def get(self, req: models.RetailCustomerGet | dict[str, Any]) -> models.RetailCustomerRegosOffsettedArrayResult:
        """POST RetailCustomer/Get."""
        return await self._call(self.PATH_GET, req, models.RetailCustomerRegosOffsettedArrayResult)

    async def add(self, req: models.RetailCustomerAdd | dict[str, Any]) -> models.InsertResult:
        """POST RetailCustomer/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.RetailCustomerEdit | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCustomer/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.RetailCustomerDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCustomer/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.RetailCustomerDelete | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCustomer/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def get_favorite_purchases(self, req: models.RetailCustomerPurchaseRequest | dict[str, Any]) -> models.RetailCustomerItemPurchasesArrayRegosObjectResult:
        """POST RetailCustomer/GetFavoritePurchases."""
        return await self._call(self.PATH_GET_FAVORITE_PURCHASES, req, models.RetailCustomerItemPurchasesArrayRegosObjectResult)

    async def get_avg_cheque_amount(self, req: models.RetailCustomerPurchaseRequest | dict[str, Any]) -> models.DecimalRegosObjectResult:
        """POST RetailCustomer/GetAvgChequeAmount."""
        return await self._call(self.PATH_GET_AVG_CHEQUE_AMOUNT, req, models.DecimalRegosObjectResult)

    async def get_last_purchase_date(self, req: models.RetailCustomerPurchaseRequest | dict[str, Any]) -> models.Int64RegosObjectResult:
        """POST RetailCustomer/GetLastPurchaseDate."""
        return await self._call(self.PATH_GET_LAST_PURCHASE_DATE, req, models.Int64RegosObjectResult)

    async def get_cheque_count(self, req: models.RetailCustomerPurchaseRequest | dict[str, Any]) -> models.Int64RegosObjectResult:
        """POST RetailCustomer/GetChequeCount."""
        return await self._call(self.PATH_GET_CHEQUE_COUNT, req, models.Int64RegosObjectResult)

    async def get_purchase_info(self, req: models.RetailCustomerPurchaseInfoRequest | dict[str, Any]) -> models.RetailCustomerPurchaseInfoRegosObjectResult:
        """POST RetailCustomer/GetPurchaseInfo."""
        return await self._call(self.PATH_GET_PURCHASE_INFO, req, models.RetailCustomerPurchaseInfoRegosObjectResult)

    async def get_debts(self, req: models.RetailCustomerDebtRecordGet | dict[str, Any]) -> models.RetailCustomerDebtRecordRegosArrayResult:
        """POST RetailCustomer/GetDebts."""
        return await self._call(self.PATH_GET_DEBTS, req, models.RetailCustomerDebtRecordRegosArrayResult)

    async def get_debts_payment_history(self, req: models.RetailCustomerDebtPaymentsdGet | dict[str, Any]) -> models.RetailCustomerDebtPaymentRegosArrayResult:
        """POST RetailCustomer/GetDebtsPaymentHistory."""
        return await self._call(self.PATH_GET_DEBTS_PAYMENT_HISTORY, req, models.RetailCustomerDebtPaymentRegosArrayResult)

    async def add_debt(self, req: models.RetailCustomerDebtAdd | dict[str, Any]) -> models.InsertResult:
        """POST RetailCustomer/AddDebt."""
        return await self._call(self.PATH_ADD_DEBT, req, models.InsertResult)

    async def add_debt_payment(self, req: models.RetailCustomerDebtPaymentAdd | dict[str, Any]) -> models.InsertResult:
        """POST RetailCustomer/AddDebtPayment."""
        return await self._call(self.PATH_ADD_DEBT_PAYMENT, req, models.InsertResult)

__all__ = ['RetailCustomerService']
