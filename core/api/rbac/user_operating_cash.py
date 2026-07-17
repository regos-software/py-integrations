"""REGOS API service for UserOperatingCash."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserOperatingCashService(RegosAPIService):
    PATH_GET = "UserOperatingCash/Get"
    PATH_SET = "UserOperatingCash/Set"
    PATH_REMOVE = "UserOperatingCash/Remove"
    REQUEST_MODELS = {
        'get': models.UserOperatingCashGet,
        'remove': models.UserOperatingCashRemove,
        'set': models.UserOperatingCashSet,
    }

    async def get(self, req: models.UserOperatingCashGet | dict[str, Any]) -> models.UserOperatingCashRegosOffsettedArrayResult:
        """POST UserOperatingCash/Get."""
        return await self._call(self.PATH_GET, req, models.UserOperatingCashRegosOffsettedArrayResult)

    async def set(self, req: models.UserOperatingCashSet | dict[str, Any]) -> models.InsertResult:
        """POST UserOperatingCash/Set."""
        return await self._call(self.PATH_SET, req, models.InsertResult)

    async def remove(self, req: models.UserOperatingCashRemove | dict[str, Any]) -> models.UpdateResult:
        """POST UserOperatingCash/Remove."""
        return await self._call(self.PATH_REMOVE, req, models.UpdateResult)

__all__ = ['UserOperatingCashService']
