"""REGOS API service for File."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class FileService(RegosAPIService):
    PATH_GET = "File/Get"
    PATH_ADD = "File/Add"
    PATH_EDIT = "File/Edit"
    PATH_DELETE = "File/Delete"
    REQUEST_MODELS = {
        'delete': models.CommonFileDelete,
        'edit': models.CommonFileEdit,
        'get': models.CommonFileGet,
    }

    async def get(self, req: models.CommonFileGet | dict[str, Any]) -> models.CommonFileRegosOffsettedArrayResult:
        """POST File/Get."""
        return await self._call(self.PATH_GET, req, models.CommonFileRegosOffsettedArrayResult)

    async def add(self, body: dict[str, Any] | None = None) -> models.InsertResult:
        """POST File/Add."""
        return await self._call(self.PATH_ADD, body or {}, models.InsertResult)

    async def edit(self, req: models.CommonFileEdit | dict[str, Any]) -> models.UpdateResult:
        """POST File/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.CommonFileDelete | dict[str, Any]) -> models.UpdateResult:
        """POST File/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['FileService']
