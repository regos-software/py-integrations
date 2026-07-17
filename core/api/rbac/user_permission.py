"""REGOS API service for UserPermission."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserPermissionService(RegosAPIService):
    PATH_GET_EXT = "UserPermission/GetExt"
    REQUEST_MODELS = {
        'get_ext': models.UserPermissionGetEx,
    }

    async def get_ext(self, req: models.UserPermissionGetEx | dict[str, Any]) -> models.UserPermissionExtArrayRegosObjectResult:
        """POST UserPermission/GetExt."""
        return await self._call(self.PATH_GET_EXT, req, models.UserPermissionExtArrayRegosObjectResult)

__all__ = ['UserPermissionService']
