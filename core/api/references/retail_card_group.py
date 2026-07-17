"""REGOS API service for RetailCardGroup."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RetailCardGroupService(RegosAPIService):
    PATH_GET = "RetailCardGroup/Get"
    PATH_ADD = "RetailCardGroup/Add"
    PATH_EDIT = "RetailCardGroup/Edit"
    PATH_DELETE = "RetailCardGroup/Delete"
    REQUEST_MODELS = {
        'add': models.RetailCardGroupAdd,
        'delete': models.RetailCardGroupDelete,
        'edit': models.RetailCardGroupEdit,
        'get': models.RetailCardGroupGet,
    }

    async def get(self, req: models.RetailCardGroupGet | dict[str, Any]) -> models.RetailCardGroupArrayRegosObjectResult:
        """POST RetailCardGroup/Get."""
        return await self._call(self.PATH_GET, req, models.RetailCardGroupArrayRegosObjectResult)

    async def add(self, req: models.RetailCardGroupAdd | dict[str, Any]) -> models.InsertResult:
        """POST RetailCardGroup/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.RetailCardGroupEdit | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCardGroup/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.RetailCardGroupDelete | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCardGroup/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['RetailCardGroupService']
