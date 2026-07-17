"""REGOS API service for Redefinition."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RedefinitionService(RegosAPIService):
    PATH_GET = "Redefinition/Get"
    PATH_ADD = "Redefinition/Add"
    PATH_EDIT = "Redefinition/Edit"
    PATH_DELETE = "Redefinition/Delete"
    REQUEST_MODELS = {
        'add': models.Redefinition_Add,
        'delete': models.Redefinition_Delete,
        'edit': models.Redefinition_Edit,
        'get': models.Redefinition_Get,
    }

    async def get(self, req: models.Redefinition_Get | dict[str, Any]) -> models.RedefinitionRegosArrayResult:
        """POST Redefinition/Get."""
        return await self._call(self.PATH_GET, req, models.RedefinitionRegosArrayResult)

    async def add(self, req: models.Redefinition_Add | dict[str, Any]) -> models.InsertResult:
        """POST Redefinition/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.Redefinition_Edit | dict[str, Any]) -> models.UpdateResult:
        """POST Redefinition/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.Redefinition_Delete | dict[str, Any]) -> models.UpdateResult:
        """POST Redefinition/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['RedefinitionService']
