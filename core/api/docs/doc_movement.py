"""REGOS API service for DocMovement."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocMovementService(RegosAPIService):
    PATH_GET = "DocMovement/Get"
    PATH_ADD = "DocMovement/Add"
    PATH_EDIT = "DocMovement/Edit"
    PATH_DELETE_MARK = "DocMovement/DeleteMark"
    PATH_DELETE = "DocMovement/Delete"
    PATH_LOCK = "DocMovement/Lock"
    PATH_UNLOCK = "DocMovement/Unlock"
    PATH_PERFORM = "DocMovement/Perform"
    PATH_PERFORM_CANCEL = "DocMovement/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocMovementAdd,
        'delete': models.DocMovementDelete,
        'delete_mark': models.DocMovementDeleteMark,
        'edit': models.DocMovementEdit,
        'get': models.DocMovementGet,
        'lock': models.DocMovementLockAndUnlock,
        'perform': models.DocMovementPerformAndCancel,
        'perform_cancel': models.DocMovementPerformAndCancel,
        'unlock': models.DocMovementLockAndUnlock,
    }

    async def get(self, req: models.DocMovementGet | dict[str, Any]) -> models.DocMovementRegosOffsettedArrayResult:
        """POST DocMovement/Get."""
        return await self._call(self.PATH_GET, req, models.DocMovementRegosOffsettedArrayResult)

    async def add(self, req: models.DocMovementAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocMovement/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocMovementEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocMovement/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocMovementDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocMovement/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocMovementDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocMovement/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocMovementLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocMovement/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocMovementLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocMovement/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.DocMovementPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocMovement/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocMovementPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocMovement/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocMovementService']
