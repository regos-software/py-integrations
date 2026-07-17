"""REGOS API service for StockAgregationOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class StockAgregationOperationService(RegosAPIService):
    PATH_GET = "StockAgregationOperation/Get"
    REQUEST_MODELS = {
        'get': models.StockAgregationOperationGet,
    }

    async def get(self, req: models.StockAgregationOperationGet | dict[str, Any]) -> models.StockAgregationOperationRegosOffsettedArrayResult:
        """POST StockAgregationOperation/Get."""
        return await self._call(self.PATH_GET, req, models.StockAgregationOperationRegosOffsettedArrayResult)

__all__ = ['StockAgregationOperationService']
