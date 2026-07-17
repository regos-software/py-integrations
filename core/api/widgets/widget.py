"""REGOS API service for Widget."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class WidgetService(RegosAPIService):
    PATH_GET = "Widget/Get"
    PATH_ADD = "Widget/Add"
    PATH_EDIT = "Widget/Edit"
    PATH_DELETE = "Widget/Delete"
    PATH_SET_FILTERS = "Widget/SetFilters"
    PATH_SET_POSITION = "Widget/SetPosition"
    REQUEST_MODELS = {
        'edit': models.WidgetEdit,
        'get': models.WidgetGet,
        'set_filters': models.WidgetSetFilters,
    }

    async def get(self, req: models.WidgetGet | dict[str, Any]) -> models.WidgetRegosArrayResult:
        """POST Widget/Get."""
        return await self._call(self.PATH_GET, req, models.WidgetRegosArrayResult)

    async def add(self, req: list[models.WidgetAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST Widget/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: models.WidgetEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Widget/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.Base_ID] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST Widget/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_filters(self, req: models.WidgetSetFilters | dict[str, Any]) -> models.SingleObjectResult:
        """POST Widget/SetFilters."""
        return await self._call(self.PATH_SET_FILTERS, req, models.SingleObjectResult)

    async def set_position(self, req: list[models.WidgetSetPosition] | list[dict[str, Any]]) -> models.SingleObjectResult:
        """POST Widget/SetPosition."""
        return await self._call(self.PATH_SET_POSITION, req, models.SingleObjectResult)

__all__ = ['WidgetService']
