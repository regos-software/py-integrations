"""REGOS API service for PromoProgramStock."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PromoProgramStockService(RegosAPIService):
    PATH_GET = "PromoProgramStock/Get"
    PATH_SET = "PromoProgramStock/Set"
    PATH_DELETE = "PromoProgramStock/Delete"
    REQUEST_MODELS = {
        'get': models.Promo_ProgramStock_Get,
    }

    async def get(self, req: models.Promo_ProgramStock_Get | dict[str, Any]) -> models.Promo_ProgramStockRegosArrayResult:
        """POST PromoProgramStock/Get."""
        return await self._call(self.PATH_GET, req, models.Promo_ProgramStockRegosArrayResult)

    async def set(self, req: list[models.Promo_ProgramStock_Set] | list[dict[str, Any]]) -> models.InsertResult:
        """POST PromoProgramStock/Set."""
        return await self._call(self.PATH_SET, req, models.InsertResult)

    async def delete(self, req: list[models.Promo_ProgramStock_Remove] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST PromoProgramStock/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['PromoProgramStockService']
