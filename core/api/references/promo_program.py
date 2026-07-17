"""REGOS API service for PromoProgram."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PromoProgramService(RegosAPIService):
    PATH_GET = "PromoProgram/Get"
    PATH_ADD = "PromoProgram/Add"
    PATH_EDIT = "PromoProgram/Edit"
    PATH_DELETE = "PromoProgram/Delete"
    REQUEST_MODELS = {
        'add': models.PromoProgramAdd,
        'delete': models.PromoProgramDelete,
        'edit': models.PromoProgramEdit,
        'get': models.PromoProgramGet,
    }

    async def get(self, req: models.PromoProgramGet | dict[str, Any]) -> models.PromoProgramArrayRegosObjectResult:
        """POST PromoProgram/Get."""
        return await self._call(self.PATH_GET, req, models.PromoProgramArrayRegosObjectResult)

    async def add(self, req: models.PromoProgramAdd | dict[str, Any]) -> models.InsertResult:
        """POST PromoProgram/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.PromoProgramEdit | dict[str, Any]) -> models.UpdateResult:
        """POST PromoProgram/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.PromoProgramDelete | dict[str, Any]) -> models.UpdateResult:
        """POST PromoProgram/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['PromoProgramService']
