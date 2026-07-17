"""REGOS API service for Unit."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UnitService(RegosAPIService):
    PATH_GET = "Unit/Get"
    PATH_ADD = "Unit/Add"
    PATH_EDIT = "Unit/Edit"
    PATH_DELETE = "Unit/Delete"
    REQUEST_MODELS = {
        'add': models.UnitAdd,
        'delete': models.UnitDelete,
        'edit': models.UnitEdit,
        'get': models.UnitGet,
    }

    async def get(self, req: models.UnitGet | dict[str, Any]) -> models.UnitRegosOffsettedArrayResult:
        """POST Unit/Get."""
        return await self._call(self.PATH_GET, req, models.UnitRegosOffsettedArrayResult)

    async def add(self, req: models.UnitAdd | dict[str, Any]) -> models.InsertResult:
        """POST Unit/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.UnitEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Unit/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.UnitDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Unit/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['UnitService']
