"""REGOS API service for DocProduction."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocProductionService(RegosAPIService):
    PATH_GET = "DocProduction/Get"
    PATH_ADD = "DocProduction/Add"
    PATH_EDIT = "DocProduction/Edit"
    PATH_DELETE = "DocProduction/Delete"
    PATH_LOCK = "DocProduction/Lock"
    PATH_UNLOCK = "DocProduction/Unlock"
    PATH_PERFORM = "DocProduction/Perform"
    PATH_PERFORM_CANCEL = "DocProduction/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocProduction_Add,
        'delete': models.Base_ID,
        'edit': models.DocProduction_Edit,
        'get': models.DocProduction_Get,
        'lock': models.Base_ID,
        'perform': models.Base_ID,
        'perform_cancel': models.Base_ID,
        'unlock': models.Base_ID,
    }

    async def get(self, req: models.DocProduction_Get | dict[str, Any]) -> models.DocProductionRegosOffsettedArrayResult:
        """POST DocProduction/Get."""
        return await self._call(self.PATH_GET, req, models.DocProductionRegosOffsettedArrayResult)

    async def add(self, req: models.DocProduction_Add | dict[str, Any]) -> models.InsertResult:
        """POST DocProduction/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocProduction_Edit | dict[str, Any]) -> models.UpdateResult:
        """POST DocProduction/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocProduction/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocProduction/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocProduction/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocProduction/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocProduction/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocProductionService']
