"""REGOS API service for UserStock."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserStockService(RegosAPIService):
    PATH_GET = "UserStock/Get"
    PATH_SET = "UserStock/Set"
    PATH_REMOVE = "UserStock/remove"
    REQUEST_MODELS = {
        'get': models.UserStockGet,
        'remove': models.UserStockRemove,
        'set': models.UserStockSet,
    }

    async def get(self, req: models.UserStockGet | dict[str, Any]) -> models.UserStockRegosArrayResult:
        """POST UserStock/Get."""
        return await self._call(self.PATH_GET, req, models.UserStockRegosArrayResult)

    async def set(self, req: models.UserStockSet | dict[str, Any]) -> models.InsertResult:
        """POST UserStock/Set."""
        return await self._call(self.PATH_SET, req, models.InsertResult)

    async def remove(self, req: models.UserStockRemove | dict[str, Any]) -> models.UpdateResult:
        """POST UserStock/remove."""
        return await self._call(self.PATH_REMOVE, req, models.UpdateResult)

__all__ = ['UserStockService']
