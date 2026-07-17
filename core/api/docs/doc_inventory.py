"""REGOS API service for DocInventory."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocInventoryService(RegosAPIService):
    PATH_GET = "DocInventory/Get"
    PATH_ADD = "DocInventory/Add"
    PATH_EDIT = "DocInventory/Edit"
    PATH_DELETE_MARK = "DocInventory/DeleteMark"
    PATH_DELETE = "DocInventory/Delete"
    PATH_LOCK = "DocInventory/Lock"
    PATH_UNLOCK = "DocInventory/Unlock"
    PATH_CLOSE = "DocInventory/Close"
    PATH_OPEN = "DocInventory/Open"
    REQUEST_MODELS = {
        'add': models.DocInventoryAdd,
        'close': models.DocInventoryCloseAndOpen,
        'delete': models.DocInventoryDelete,
        'delete_mark': models.DocInventoryDeleteMark,
        'edit': models.DocInventoryEdit,
        'get': models.DocInventoryGet,
        'lock': models.DocInventoryLockAndUnlock,
        'open': models.DocInventoryCloseAndOpen,
        'unlock': models.DocInventoryLockAndUnlock,
    }

    async def get(self, req: models.DocInventoryGet | dict[str, Any]) -> models.DocInventoryRegosOffsettedArrayResult:
        """POST DocInventory/Get."""
        return await self._call(self.PATH_GET, req, models.DocInventoryRegosOffsettedArrayResult)

    async def add(self, req: models.DocInventoryAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocInventory/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocInventoryEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocInventory/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocInventoryDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocInventory/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocInventoryDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocInventory/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocInventoryLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocInventory/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocInventoryLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocInventory/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def close(self, req: models.DocInventoryCloseAndOpen | dict[str, Any]) -> models.UpdateResult:
        """POST DocInventory/Close."""
        return await self._call(self.PATH_CLOSE, req, models.UpdateResult)

    async def open(self, req: models.DocInventoryCloseAndOpen | dict[str, Any]) -> models.UpdateResult:
        """POST DocInventory/Open."""
        return await self._call(self.PATH_OPEN, req, models.UpdateResult)

__all__ = ['DocInventoryService']
