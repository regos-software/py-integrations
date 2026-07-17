"""REGOS API service for DocPaymentAggregation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocPaymentAggregationService(RegosAPIService):
    PATH_GET = "DocPaymentAggregation/Get"
    REQUEST_MODELS = {
        'get': models.DocPaymentAggregationGet,
    }

    async def get(self, req: models.DocPaymentAggregationGet | dict[str, Any]) -> models.DocPaymentAggregationRegosOffsettedArrayResult:
        """POST DocPaymentAggregation/Get."""
        return await self._call(self.PATH_GET, req, models.DocPaymentAggregationRegosOffsettedArrayResult)

__all__ = ['DocPaymentAggregationService']
