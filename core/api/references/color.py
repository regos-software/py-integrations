"""REGOS API service for Color."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ColorService(RegosAPIService):
    PATH_GET = "Color/Get"
    PATH_ADD = "Color/Add"
    PATH_EDIT = "Color/Edit"
    PATH_DELETE = "Color/Delete"
    REQUEST_MODELS = {
        'add': models.ColorAdd,
        'delete': models.ColorDelete,
        'edit': models.ColorEdit,
        'get': models.ColorGet,
    }

    async def get(self, req: models.ColorGet | dict[str, Any]) -> models.ColorRegosOffsettedArrayResult:
        """POST Color/Get."""
        return await self._call(self.PATH_GET, req, models.ColorRegosOffsettedArrayResult)

    async def add(self, req: models.ColorAdd | dict[str, Any]) -> models.InsertResult:
        """POST Color/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.ColorEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Color/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.ColorDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Color/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['ColorService']
