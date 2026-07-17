"""REGOS API service for PosCashOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PosCashOperationService(RegosAPIService):
    PATH_GET = "pos/CashOperation/Get"
    PATH_GET_AMOUNT_DETAILS = "pos/CashOperation/GetAmountDetails"
    PATH_INCOME_ADD = "pos/CashOperation/IncomeAdd"
    PATH_OUTCOME_ADD = "pos/CashOperation/OutcomeAdd"
    PATH_PAYMENT_ADD = "pos/CashOperation/PaymentAdd"
    REQUEST_MODELS = {
        'get': models.RegosOnlineCashOperationGet,
        'get_amount_details': models.RegosOnlineCashAmountDetailsGet,
        'income_add': models.RegosOnlineCashOperationAdd,
        'outcome_add': models.RegosOnlineCashOperationAdd,
        'payment_add': models.RegosOnlineCashOperationPaymentAdd,
    }

    async def get(self, req: models.RegosOnlineCashOperationGet | dict[str, Any]) -> models.CashOperationRegosOffsettedArrayResult:
        """POST pos/CashOperation/Get."""
        return await self._call(self.PATH_GET, req, models.CashOperationRegosOffsettedArrayResult)

    async def get_amount_details(self, req: models.RegosOnlineCashAmountDetailsGet | dict[str, Any]) -> models.CashAmountDetailsRegosObjectResult:
        """POST pos/CashOperation/GetAmountDetails."""
        return await self._call(self.PATH_GET_AMOUNT_DETAILS, req, models.CashAmountDetailsRegosObjectResult)

    async def income_add(self, req: models.RegosOnlineCashOperationAdd | dict[str, Any]) -> models.InsertResult:
        """POST pos/CashOperation/IncomeAdd."""
        return await self._call(self.PATH_INCOME_ADD, req, models.InsertResult)

    async def outcome_add(self, req: models.RegosOnlineCashOperationAdd | dict[str, Any]) -> models.InsertResult:
        """POST pos/CashOperation/OutcomeAdd."""
        return await self._call(self.PATH_OUTCOME_ADD, req, models.InsertResult)

    async def payment_add(self, req: models.RegosOnlineCashOperationPaymentAdd | dict[str, Any]) -> models.InsertResult:
        """POST pos/CashOperation/PaymentAdd."""
        return await self._call(self.PATH_PAYMENT_ADD, req, models.InsertResult)

__all__ = ['PosCashOperationService']
