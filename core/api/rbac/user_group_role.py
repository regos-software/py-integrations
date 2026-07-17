"""REGOS API service for UserGroupRole."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserGroupRoleService(RegosAPIService):
    PATH_GET = "UserGroupRole/Get"
    PATH_SET = "UserGroupRole/Set"
    PATH_REMOVE = "UserGroupRole/remove"
    REQUEST_MODELS = {
        'get': models.UserGroupRoleGet,
        'remove': models.UserGroupRoleRemove,
        'set': models.UserGroupRoleSet,
    }

    async def get(self, req: models.UserGroupRoleGet | dict[str, Any]) -> models.UserGroupRoleRegosArrayResult:
        """POST UserGroupRole/Get."""
        return await self._call(self.PATH_GET, req, models.UserGroupRoleRegosArrayResult)

    async def set(self, req: models.UserGroupRoleSet | dict[str, Any]) -> models.InsertResult:
        """POST UserGroupRole/Set."""
        return await self._call(self.PATH_SET, req, models.InsertResult)

    async def remove(self, req: models.UserGroupRoleRemove | dict[str, Any]) -> models.UpdateResult:
        """POST UserGroupRole/remove."""
        return await self._call(self.PATH_REMOVE, req, models.UpdateResult)

__all__ = ['UserGroupRoleService']
