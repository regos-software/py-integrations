"""REGOS API service for Tag."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class TagService(RegosAPIService):
    PATH_GET = "Tag/Get"
    PATH_ADD = "Tag/Add"
    PATH_EDIT = "Tag/Edit"
    PATH_DELETE = "Tag/Delete"
    REQUEST_MODELS = {
        'add': models.TagAdd,
        'delete': models.TagDelete,
        'edit': models.TagEdit,
        'get': models.TagGet,
    }

    async def get(self, req: models.TagGet | dict[str, Any]) -> models.TagRegosArrayResult:
        """POST Tag/Get."""
        return await self._call(self.PATH_GET, req, models.TagRegosArrayResult)

    async def add(self, req: models.TagAdd | dict[str, Any]) -> models.InsertResult:
        """POST Tag/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.TagEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Tag/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.TagDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Tag/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['TagService']
