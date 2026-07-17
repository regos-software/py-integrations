"""REGOS API service for ItemPrice."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ItemPriceService(RegosAPIService):
    PATH_GET = "ItemPrice/Get"
    PATH_GET_PRE_COST = "ItemPrice/GetPreCost"
    REQUEST_MODELS = {
        'get': models.ItemPriceGet,
        'get_pre_cost': models.ItemPreCostGet,
    }

    async def get(self, req: models.ItemPriceGet | dict[str, Any]) -> models.ItemPriceRegosArrayResult:
        """POST ItemPrice/Get."""
        return await self._call(self.PATH_GET, req, models.ItemPriceRegosArrayResult)

    async def get_pre_cost(self, req: models.ItemPreCostGet | dict[str, Any]) -> models.ItemPreCostArrayRegosObjectResult:
        """POST ItemPrice/GetPreCost."""
        return await self._call(self.PATH_GET_PRE_COST, req, models.ItemPreCostArrayRegosObjectResult)

__all__ = ['ItemPriceService']
