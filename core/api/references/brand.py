"""REGOS API service for Brand."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class BrandService(RegosAPIService):
    PATH_GET = "Brand/Get"
    PATH_ADD = "Brand/Add"
    PATH_EDIT = "Brand/Edit"
    PATH_DELETE = "Brand/Delete"
    REQUEST_MODELS = {
        'add': models.BrandAdd,
        'delete': models.BrandDelete,
        'edit': models.BrandEdit,
        'get': models.BrandGet,
    }

    async def get(self, req: models.BrandGet | dict[str, Any]) -> models.BrandRegosOffsettedArrayResult:
        """POST Brand/Get."""
        return await self._call(self.PATH_GET, req, models.BrandRegosOffsettedArrayResult)

    async def add(self, req: models.BrandAdd | dict[str, Any]) -> models.InsertResult:
        """POST Brand/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.BrandEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Brand/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.BrandDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Brand/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['BrandService']
