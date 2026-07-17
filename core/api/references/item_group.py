"""REGOS API service for ItemGroup."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ItemGroupService(RegosAPIService):
    PATH_GET = "ItemGroup/Get"
    PATH_ADD = "ItemGroup/Add"
    PATH_EDIT = "ItemGroup/Edit"
    PATH_DELETE = "ItemGroup/Delete"
    REQUEST_MODELS = {
        'add': models.ItemGroupAdd,
        'delete': models.ItemGroupDelete,
        'edit': models.ItemGroupEdit,
        'get': models.ItemGroupGet,
    }

    async def get(self, req: models.ItemGroupGet | dict[str, Any]) -> models.ItemGroupArrayRegosObjectResult:
        """POST ItemGroup/Get."""
        return await self._call(self.PATH_GET, req, models.ItemGroupArrayRegosObjectResult)

    async def add(self, req: models.ItemGroupAdd | dict[str, Any]) -> models.InsertResult:
        """POST ItemGroup/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.ItemGroupEdit | dict[str, Any]) -> models.UpdateResult:
        """POST ItemGroup/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.ItemGroupDelete | dict[str, Any]) -> models.UpdateResult:
        """POST ItemGroup/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['ItemGroupService']
