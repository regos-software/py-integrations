"""REGOS API service for Folder."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class FolderService(RegosAPIService):
    PATH_GET = "Folder/Get"
    PATH_ADD = "Folder/Add"
    PATH_EDIT = "Folder/Edit"
    PATH_DELETE = "Folder/Delete"
    REQUEST_MODELS = {
        'add': models.CommonFolderAdd,
        'delete': models.CommonFolderDelete,
        'edit': models.CommonFolderEdit,
        'get': models.CommonFolderGet,
    }

    async def get(self, req: models.CommonFolderGet | dict[str, Any]) -> models.CommonFolderRegosOffsettedArrayResult:
        """POST Folder/Get."""
        return await self._call(self.PATH_GET, req, models.CommonFolderRegosOffsettedArrayResult)

    async def add(self, req: models.CommonFolderAdd | dict[str, Any]) -> models.InsertResult:
        """POST Folder/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.CommonFolderEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Folder/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.CommonFolderDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Folder/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['FolderService']
