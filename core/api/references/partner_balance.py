"""REGOS API service for PartnerBalance."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PartnerBalanceService(RegosAPIService):
    PATH_GET = "PartnerBalance/Get"
    PATH_GET_IN_BASE_CURRENCY = "PartnerBalance/GetInBaseCurrency"
    REQUEST_MODELS = {
        'get': models.PartnerBalanceGet,
        'get_in_base_currency': models.PartnerBalanceBaseGet,
    }

    async def get(self, req: models.PartnerBalanceGet | dict[str, Any]) -> models.PartnerBalanceRegosArrayResult:
        """POST PartnerBalance/Get."""
        return await self._call(self.PATH_GET, req, models.PartnerBalanceRegosArrayResult)

    async def get_in_base_currency(self, req: models.PartnerBalanceBaseGet | dict[str, Any]) -> models.PartnerBalanceBaseRegosArrayResult:
        """POST PartnerBalance/GetInBaseCurrency."""
        return await self._call(self.PATH_GET_IN_BASE_CURRENCY, req, models.PartnerBalanceBaseRegosArrayResult)

__all__ = ['PartnerBalanceService']
