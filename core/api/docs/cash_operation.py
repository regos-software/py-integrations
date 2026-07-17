"""REGOS API service for CashOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class CashOperationService(RegosAPIService):
    PATH_GET = "CashOperation/Get"
    PATH_GET_AMOUNT_DETAILS = "CashOperation/GetAmountDetails"
    REQUEST_MODELS = {
        'get': models.CashOperationGet,
        'get_amount_details': models.CashAmountDetailsGet,
    }

    async def get(self, req: models.CashOperationGet | dict[str, Any]) -> models.CashOperationRegosOffsettedArrayResult:
        """POST CashOperation/Get."""
        return await self._call(self.PATH_GET, req, models.CashOperationRegosOffsettedArrayResult)

    async def get_amount_details(self, req: models.CashAmountDetailsGet | dict[str, Any]) -> models.CashAmountDetailsRegosObjectResult:
        """POST CashOperation/GetAmountDetails."""
        return await self._call(self.PATH_GET_AMOUNT_DETAILS, req, models.CashAmountDetailsRegosObjectResult)

__all__ = ['CashOperationService']
