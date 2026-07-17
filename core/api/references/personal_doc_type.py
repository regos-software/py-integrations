"""REGOS API service for PersonalDocType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PersonalDocTypeService(RegosAPIService):
    PATH_GET = "PersonalDocType/Get"
    PATH_ADD = "PersonalDocType/Add"
    PATH_EDIT = "PersonalDocType/Edit"
    PATH_DELETE = "PersonalDocType/Delete"
    REQUEST_MODELS = {
        'add': models.PersonalDocTypeAdd,
        'delete': models.PersonalDocTypeDelete,
        'edit': models.PersonalDocTypeEdit,
        'get': models.PersonalDocTypeGet,
    }

    async def get(self, req: models.PersonalDocTypeGet | dict[str, Any]) -> models.PersonalDocTypeArrayRegosObjectResult:
        """POST PersonalDocType/Get."""
        return await self._call(self.PATH_GET, req, models.PersonalDocTypeArrayRegosObjectResult)

    async def add(self, req: models.PersonalDocTypeAdd | dict[str, Any]) -> models.InsertResult:
        """POST PersonalDocType/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.PersonalDocTypeEdit | dict[str, Any]) -> models.UpdateResult:
        """POST PersonalDocType/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.PersonalDocTypeDelete | dict[str, Any]) -> models.UpdateResult:
        """POST PersonalDocType/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['PersonalDocTypeService']
