"""REGOS API service for DocPurchase."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocPurchaseService(RegosAPIService):
    PATH_GET = "DocPurchase/Get"
    PATH_ADD = "DocPurchase/Add"
    PATH_EDIT = "DocPurchase/Edit"
    PATH_DELETE_MARK = "DocPurchase/DeleteMark"
    PATH_DELETE = "DocPurchase/Delete"
    PATH_LOCK = "DocPurchase/Lock"
    PATH_UNLOCK = "DocPurchase/Unlock"
    PATH_PERFORM = "DocPurchase/Perform"
    PATH_PERFORM_CANCEL = "DocPurchase/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocPurchaseAdd,
        'delete': models.Base_ID,
        'delete_mark': models.Base_ID,
        'edit': models.DocPurchaseEdit,
        'get': models.DocPurchaseGet,
        'lock': models.BaseLockAndUnlock,
        'perform': models.Base_ID,
        'perform_cancel': models.Base_ID,
        'unlock': models.BaseLockAndUnlock,
    }

    async def get(self, req: models.DocPurchaseGet | dict[str, Any]) -> models.DocPurchaseRegosOffsettedArrayResult:
        """POST DocPurchase/Get."""
        return await self._call(self.PATH_GET, req, models.DocPurchaseRegosOffsettedArrayResult)

    async def add(self, req: models.DocPurchaseAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocPurchase/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocPurchaseEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocPurchase/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocPurchase/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocPurchase/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.BaseLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocPurchase/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.BaseLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocPurchase/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocPurchase/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocPurchase/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocPurchaseService']
