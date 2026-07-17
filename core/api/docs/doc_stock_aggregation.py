"""REGOS API service for DocStockAggregation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocStockAggregationService(RegosAPIService):
    PATH_GET = "DocStockAggregation/Get"
    REQUEST_MODELS = {
        'get': models.DocStockAggregationGet,
    }

    async def get(self, req: models.DocStockAggregationGet | dict[str, Any]) -> models.DocStockAggregationRegosOffsettedArrayResult:
        """POST DocStockAggregation/Get."""
        return await self._call(self.PATH_GET, req, models.DocStockAggregationRegosOffsettedArrayResult)

__all__ = ['DocStockAggregationService']
