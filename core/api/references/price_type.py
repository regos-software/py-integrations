"""REGOS API service for PriceType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PriceTypeService(RegosAPIService):
    PATH_GET = "PriceType/Get"
    PATH_ADD = "PriceType/Add"
    PATH_EDIT = "PriceType/Edit"
    PATH_DELETE = "PriceType/Delete"
    REQUEST_MODELS = {
        'add': models.PriceTypeAdd,
        'delete': models.PriceTypeDelete,
        'edit': models.PriceTypeEdit,
        'get': models.PriceTypeGet,
    }

    async def get(self, req: models.PriceTypeGet | dict[str, Any]) -> models.PriceTypeRegosOffsettedArrayResult:
        """POST PriceType/Get."""
        return await self._call(self.PATH_GET, req, models.PriceTypeRegosOffsettedArrayResult)

    async def add(self, req: models.PriceTypeAdd | dict[str, Any]) -> models.InsertResult:
        """POST PriceType/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.PriceTypeEdit | dict[str, Any]) -> models.UpdateResult:
        """POST PriceType/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.PriceTypeDelete | dict[str, Any]) -> models.UpdateResult:
        """POST PriceType/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['PriceTypeService']
