"""REGOS API service for UserRole."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserRoleService(RegosAPIService):
    PATH_GET = "UserRole/Get"
    PATH_SET = "UserRole/Set"
    PATH_REMOVE = "UserRole/Remove"
    REQUEST_MODELS = {
        'get': models.UserRoleGet,
        'remove': models.UserRoleRemove,
        'set': models.UserRoleSet,
    }

    async def get(self, req: models.UserRoleGet | dict[str, Any]) -> models.UserRoleRegosArrayResult:
        """POST UserRole/Get."""
        return await self._call(self.PATH_GET, req, models.UserRoleRegosArrayResult)

    async def set(self, req: models.UserRoleSet | dict[str, Any]) -> models.InsertResult:
        """POST UserRole/Set."""
        return await self._call(self.PATH_SET, req, models.InsertResult)

    async def remove(self, req: models.UserRoleRemove | dict[str, Any]) -> models.UpdateResult:
        """POST UserRole/Remove."""
        return await self._call(self.PATH_REMOVE, req, models.UpdateResult)

__all__ = ['UserRoleService']
