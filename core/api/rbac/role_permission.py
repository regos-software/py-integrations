"""REGOS API service for RolePermission."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RolePermissionService(RegosAPIService):
    PATH_GET = "RolePermission/Get"
    PATH_EDIT = "RolePermission/Edit"
    REQUEST_MODELS = {
        'get': models.RolePermissionGet,
    }

    async def get(self, req: models.RolePermissionGet | dict[str, Any]) -> models.RolePermissionRegosOffsettedArrayResult:
        """POST RolePermission/Get."""
        return await self._call(self.PATH_GET, req, models.RolePermissionRegosOffsettedArrayResult)

    async def edit(self, req: list[models.RolePermissionEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST RolePermission/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

__all__ = ['RolePermissionService']
