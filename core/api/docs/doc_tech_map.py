"""REGOS API service for DocTechMap."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocTechMapService(RegosAPIService):
    PATH_GET = "DocTechMap/Get"
    PATH_ADD = "DocTechMap/Add"
    PATH_EDIT = "DocTechMap/Edit"
    PATH_DELETE = "DocTechMap/Delete"
    PATH_LOCK = "DocTechMap/Lock"
    PATH_UNLOCK = "DocTechMap/Unlock"
    PATH_PERFORM = "DocTechMap/Perform"
    PATH_PERFORM_CANCEL = "DocTechMap/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocTechMapAdd,
        'delete': models.DocTechMapId,
        'edit': models.DocTechMapEdit,
        'get': models.DocTechMapGet,
        'lock': models.DocTechMapId,
        'perform': models.DocTechMapId,
        'perform_cancel': models.DocTechMapId,
        'unlock': models.DocTechMapId,
    }

    async def get(self, req: models.DocTechMapGet | dict[str, Any]) -> models.DocTechMapRegosOffsettedArrayResult:
        """POST DocTechMap/Get."""
        return await self._call(self.PATH_GET, req, models.DocTechMapRegosOffsettedArrayResult)

    async def add(self, req: models.DocTechMapAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocTechMap/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocTechMapEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocTechMap/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.DocTechMapId | dict[str, Any]) -> models.UpdateResult:
        """POST DocTechMap/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocTechMapId | dict[str, Any]) -> models.UpdateResult:
        """POST DocTechMap/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocTechMapId | dict[str, Any]) -> models.UpdateResult:
        """POST DocTechMap/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.DocTechMapId | dict[str, Any]) -> models.UpdateResult:
        """POST DocTechMap/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocTechMapId | dict[str, Any]) -> models.UpdateResult:
        """POST DocTechMap/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocTechMapService']
