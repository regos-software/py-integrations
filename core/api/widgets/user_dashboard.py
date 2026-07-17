"""REGOS API service for UserDashboard."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserDashboardService(RegosAPIService):
    PATH_GET = "UserDashboard/Get"
    PATH_SET = "UserDashboard/Set"
    PATH_REMOVE = "UserDashboard/remove"
    PATH_SET_DEFAULT = "UserDashboard/SetDefault"
    REQUEST_MODELS = {
        'get': models.UserDashboardGet,
        'remove': models.UserDashboardRemove,
        'set': models.UserDashboardSet,
        'set_default': models.UserDashboardSetDefault,
    }

    async def get(self, req: models.UserDashboardGet | dict[str, Any]) -> models.UserDashboardRegosArrayResult:
        """POST UserDashboard/Get."""
        return await self._call(self.PATH_GET, req, models.UserDashboardRegosArrayResult)

    async def set(self, req: models.UserDashboardSet | dict[str, Any]) -> models.InsertResult:
        """POST UserDashboard/Set."""
        return await self._call(self.PATH_SET, req, models.InsertResult)

    async def remove(self, req: models.UserDashboardRemove | dict[str, Any]) -> models.UpdateResult:
        """POST UserDashboard/remove."""
        return await self._call(self.PATH_REMOVE, req, models.UpdateResult)

    async def set_default(self, req: models.UserDashboardSetDefault | dict[str, Any]) -> models.UpdateResult:
        """POST UserDashboard/SetDefault."""
        return await self._call(self.PATH_SET_DEFAULT, req, models.UpdateResult)

__all__ = ['UserDashboardService']
