"""REGOS API service for PermissionGroup."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PermissionGroupService(RegosAPIService):
    PATH_GET = "PermissionGroup/Get"
    REQUEST_MODELS = {
        'get': models.PermissionGroupGet,
    }

    async def get(self, req: models.PermissionGroupGet | dict[str, Any]) -> models.PermissionGroupRegosArrayResult:
        """POST PermissionGroup/Get."""
        return await self._call(self.PATH_GET, req, models.PermissionGroupRegosArrayResult)

__all__ = ['PermissionGroupService']
