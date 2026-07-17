"""REGOS API service for Field."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class FieldService(RegosAPIService):
    PATH_GET = "Field/Get"
    PATH_ADD = "Field/Add"
    PATH_EDIT = "Field/Edit"
    PATH_DELETE = "Field/Delete"
    REQUEST_MODELS = {
        'add': models.FieldAdd,
        'delete': models.Base_ID,
        'edit': models.FieldEdit,
        'get': models.FieldGet,
    }

    async def get(self, req: models.FieldGet | dict[str, Any]) -> models.FieldRegosArrayResult:
        """POST Field/Get."""
        return await self._call(self.PATH_GET, req, models.FieldRegosArrayResult)

    async def add(self, req: models.FieldAdd | dict[str, Any]) -> models.InsertResult:
        """POST Field/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.FieldEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Field/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST Field/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['FieldService']
