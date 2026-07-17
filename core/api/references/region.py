"""REGOS API service for Region."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RegionService(RegosAPIService):
    PATH_GET = "Region/get"
    PATH_ADD = "Region/add"
    PATH_EDIT = "Region/edit"
    PATH_DELETE = "Region/delete"
    REQUEST_MODELS = {
        'add': models.RegionAdd,
        'delete': models.RegionDelete,
        'edit': models.RegionEdit,
        'get': models.RegionGet,
    }

    async def get(self, req: models.RegionGet | dict[str, Any]) -> models.RegionRegosArrayResult:
        """POST Region/get."""
        return await self._call(self.PATH_GET, req, models.RegionRegosArrayResult)

    async def add(self, req: models.RegionAdd | dict[str, Any]) -> models.InsertResult:
        """POST Region/add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.RegionEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Region/edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.RegionDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Region/delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['RegionService']
