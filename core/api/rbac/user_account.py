"""REGOS API service for UserAccount."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserAccountService(RegosAPIService):
    PATH_GET = "UserAccount/Get"
    PATH_SET = "UserAccount/Set"
    PATH_REMOVE = "UserAccount/remove"
    REQUEST_MODELS = {
        'get': models.UserAccountGet,
        'remove': models.UserAccountRemove,
        'set': models.UserAccountSet,
    }

    async def get(self, req: models.UserAccountGet | dict[str, Any]) -> models.UserAccountRegosArrayResult:
        """POST UserAccount/Get."""
        return await self._call(self.PATH_GET, req, models.UserAccountRegosArrayResult)

    async def set(self, req: models.UserAccountSet | dict[str, Any]) -> models.InsertResult:
        """POST UserAccount/Set."""
        return await self._call(self.PATH_SET, req, models.InsertResult)

    async def remove(self, req: models.UserAccountRemove | dict[str, Any]) -> models.UpdateResult:
        """POST UserAccount/remove."""
        return await self._call(self.PATH_REMOVE, req, models.UpdateResult)

__all__ = ['UserAccountService']
