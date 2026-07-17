"""REGOS API service for DealType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DealTypeService(RegosAPIService):
    PATH_GET = "DealType/Get"
    PATH_ADD = "DealType/Add"
    PATH_EDIT = "DealType/Edit"
    PATH_DELETE = "DealType/Delete"
    REQUEST_MODELS = {
        'add': models.DealTypeAdd,
        'delete': models.DealTypeDelete,
        'edit': models.DealTypeEdit,
        'get': models.DealTypeGet,
    }

    async def get(self, req: models.DealTypeGet | dict[str, Any]) -> models.DealTypeRegosOffsettedArrayResult:
        """POST DealType/Get."""
        return await self._call(self.PATH_GET, req, models.DealTypeRegosOffsettedArrayResult)

    async def add(self, req: models.DealTypeAdd | dict[str, Any]) -> models.InsertResult:
        """POST DealType/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DealTypeEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DealType/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.DealTypeDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DealType/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DealTypeService']
