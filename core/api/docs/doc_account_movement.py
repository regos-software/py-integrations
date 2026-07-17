"""REGOS API service for DocAccountMovement."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocAccountMovementService(RegosAPIService):
    PATH_GET = "DocAccountMovement/Get"
    PATH_ADD = "DocAccountMovement/Add"
    PATH_EDIT = "DocAccountMovement/Edit"
    PATH_DELETE_MARK = "DocAccountMovement/DeleteMark"
    PATH_DELETE = "DocAccountMovement/Delete"
    PATH_PERFORM = "DocAccountMovement/Perform"
    PATH_PERFORM_CANCEL = "DocAccountMovement/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocAccountMovementAdd,
        'delete': models.DocAccountMovementDelete,
        'delete_mark': models.DocAccountMovementDeleteMark,
        'edit': models.DocAccountMovementEdit,
        'get': models.DocAccountMovementGet,
        'perform': models.DocAccountMovementPerformAndCancel,
        'perform_cancel': models.DocAccountMovementPerformAndCancel,
    }

    async def get(self, req: models.DocAccountMovementGet | dict[str, Any]) -> models.DocAccountMovementRegosOffsettedArrayResult:
        """POST DocAccountMovement/Get."""
        return await self._call(self.PATH_GET, req, models.DocAccountMovementRegosOffsettedArrayResult)

    async def add(self, req: models.DocAccountMovementAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocAccountMovement/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocAccountMovementEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocAccountMovement/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocAccountMovementDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocAccountMovement/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocAccountMovementDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocAccountMovement/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def perform(self, req: models.DocAccountMovementPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocAccountMovement/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocAccountMovementPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocAccountMovement/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocAccountMovementService']
