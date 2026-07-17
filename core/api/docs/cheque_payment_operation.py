"""REGOS API service for ChequePaymentOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ChequePaymentOperationService(RegosAPIService):
    PATH_POS_GET = "pos/ChequePaymentOperation/get"
    PATH_ADD = "pos/ChequePaymentOperation/add"
    PATH_STORNO = "pos/ChequePaymentOperation/Storno"
    PATH_GET_PAYMENT_SYSTEM_ID = "pos/ChequePaymentOperation/GetPaymentSystemId"
    PATH_GET = "ChequePaymentOperation/Get"
    REQUEST_MODELS = {
        'add': models.PaymentAdd,
        'get': models.DocRetailPaymentGet,
        'get_payment_system_id': models.PosPaymentSystemGet,
        'pos_get': models.PaymentGet,
        'storno': models.PaymentStorno,
    }

    async def pos_get(self, req: models.PaymentGet | dict[str, Any]) -> models.PaymentArrayRegosObjectResult:
        """POST pos/ChequePaymentOperation/get."""
        return await self._call(self.PATH_POS_GET, req, models.PaymentArrayRegosObjectResult)

    async def add(self, req: models.PaymentAdd | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST pos/ChequePaymentOperation/add."""
        return await self._call(self.PATH_ADD, req, models.Insert_uuid_Result)

    async def storno(self, req: models.PaymentStorno | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST pos/ChequePaymentOperation/Storno."""
        return await self._call(self.PATH_STORNO, req, models.Insert_uuid_Result)

    async def get_payment_system_id(self, req: models.PosPaymentSystemGet | dict[str, Any]) -> models.PosPaymentSystemIDRegosObjectResult:
        """POST pos/ChequePaymentOperation/GetPaymentSystemId."""
        return await self._call(self.PATH_GET_PAYMENT_SYSTEM_ID, req, models.PosPaymentSystemIDRegosObjectResult)

    async def get(self, req: models.DocRetailPaymentGet | dict[str, Any]) -> models.DocRetailPaymentRegosArrayResult:
        """POST ChequePaymentOperation/Get."""
        return await self._call(self.PATH_GET, req, models.DocRetailPaymentRegosArrayResult)

__all__ = ['ChequePaymentOperationService']
