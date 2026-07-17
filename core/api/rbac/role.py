"""REGOS API service for Role."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RoleService(RegosAPIService):
    PATH_GET = "Role/Get"
    PATH_ADD = "Role/Add"
    PATH_EDIT = "Role/Edit"
    PATH_DELETE = "Role/Delete"
    REQUEST_MODELS = {
        'add': models.RoleAdd,
        'delete': models.RoleDelete,
        'edit': models.RoleEdit,
        'get': models.RoleGet,
    }

    async def get(self, req: models.RoleGet | dict[str, Any]) -> models.RoleRegosOffsettedArrayResult:
        """POST Role/Get."""
        return await self._call(self.PATH_GET, req, models.RoleRegosOffsettedArrayResult)

    async def add(self, req: models.RoleAdd | dict[str, Any]) -> models.InsertResult:
        """POST Role/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.RoleEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Role/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.RoleDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Role/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['RoleService']
