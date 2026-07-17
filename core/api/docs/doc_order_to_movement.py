"""REGOS API service for DocOrderToMovement."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocOrderToMovementService(RegosAPIService):
    PATH_GET = "DocOrderToMovement/Get"
    PATH_ADD = "DocOrderToMovement/Add"
    PATH_EDIT = "DocOrderToMovement/Edit"
    PATH_DELETE_MARK = "DocOrderToMovement/DeleteMark"
    PATH_DELETE = "DocOrderToMovement/Delete"
    PATH_LOCK = "DocOrderToMovement/Lock"
    PATH_UNLOCK = "DocOrderToMovement/Unlock"
    REQUEST_MODELS = {
        'add': models.DocOrderToMovementAdd,
        'delete': models.DocOrderToMovementDelete,
        'delete_mark': models.DocOrderToMovementDeleteMark,
        'edit': models.DocOrderToMovementEdit,
        'get': models.DocOrderToMovementGet,
        'lock': models.DocOrderToMovementLockAndUnlock,
        'unlock': models.DocOrderToMovementLockAndUnlock,
    }

    async def get(self, req: models.DocOrderToMovementGet | dict[str, Any]) -> models.DocOrderToMovementRegosOffsettedArrayResult:
        """POST DocOrderToMovement/Get."""
        return await self._call(self.PATH_GET, req, models.DocOrderToMovementRegosOffsettedArrayResult)

    async def add(self, req: models.DocOrderToMovementAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocOrderToMovement/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocOrderToMovementEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToMovement/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocOrderToMovementDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToMovement/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocOrderToMovementDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToMovement/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocOrderToMovementLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToMovement/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocOrderToMovementLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToMovement/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

__all__ = ['DocOrderToMovementService']
