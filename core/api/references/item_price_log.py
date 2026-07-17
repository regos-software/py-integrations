"""REGOS API service for ItemPriceLog."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ItemPriceLogService(RegosAPIService):
    PATH_GET = "ItemPriceLog/Get"
    REQUEST_MODELS = {
        'get': models.ItemPriceLogGet,
    }

    async def get(self, req: models.ItemPriceLogGet | dict[str, Any]) -> models.ItemPriceLogRegosArrayResult:
        """POST ItemPriceLog/Get."""
        return await self._call(self.PATH_GET, req, models.ItemPriceLogRegosArrayResult)

__all__ = ['ItemPriceLogService']
