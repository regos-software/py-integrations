"""REGOS API service for UserGroup."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserGroupService(RegosAPIService):
    PATH_GET = "UserGroup/Get"
    PATH_ADD = "UserGroup/Add"
    PATH_EDIT = "UserGroup/Edit"
    PATH_DELETE = "UserGroup/Delete"
    REQUEST_MODELS = {
        'add': models.UserGroupAdd,
        'delete': models.UserGroupDelete,
        'edit': models.UserGroupEdit,
        'get': models.UserGroupGet,
    }

    async def get(self, req: models.UserGroupGet | dict[str, Any]) -> models.UserGroupArrayRegosObjectResult:
        """POST UserGroup/Get."""
        return await self._call(self.PATH_GET, req, models.UserGroupArrayRegosObjectResult)

    async def add(self, req: models.UserGroupAdd | dict[str, Any]) -> models.InsertResult:
        """POST UserGroup/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.UserGroupEdit | dict[str, Any]) -> models.UpdateResult:
        """POST UserGroup/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.UserGroupDelete | dict[str, Any]) -> models.UpdateResult:
        """POST UserGroup/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['UserGroupService']
