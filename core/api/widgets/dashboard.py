"""REGOS API service for Dashboard."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DashboardService(RegosAPIService):
    PATH_GET = "Dashboard/Get"
    PATH_ADD = "Dashboard/Add"
    PATH_EDIT = "Dashboard/Edit"
    PATH_DELETE = "Dashboard/Delete"
    PATH_SET_FILTERS = "Dashboard/SetFilters"
    REQUEST_MODELS = {
        'add': models.DashboardAdd,
        'delete': models.Base_ID,
        'edit': models.DashboardEdit,
        'get': models.DashboardGet,
        'set_filters': models.DashboardSetFilters,
    }

    async def get(self, req: models.DashboardGet | dict[str, Any]) -> models.DashboardRegosArrayResult:
        """POST Dashboard/Get."""
        return await self._call(self.PATH_GET, req, models.DashboardRegosArrayResult)

    async def add(self, req: models.DashboardAdd | dict[str, Any]) -> models.InsertResult:
        """POST Dashboard/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DashboardEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Dashboard/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST Dashboard/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_filters(self, req: models.DashboardSetFilters | dict[str, Any]) -> models.SingleObjectResult:
        """POST Dashboard/SetFilters."""
        return await self._call(self.PATH_SET_FILTERS, req, models.SingleObjectResult)

__all__ = ['DashboardService']
