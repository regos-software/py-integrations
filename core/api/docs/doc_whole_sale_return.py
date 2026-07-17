"""REGOS API service for DocWholeSaleReturn."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocWholeSaleReturnService(RegosAPIService):
    PATH_GET = "DocWholeSaleReturn/Get"
    PATH_ADD = "DocWholeSaleReturn/Add"
    PATH_EDIT = "DocWholeSaleReturn/Edit"
    PATH_DELETE_MARK = "DocWholeSaleReturn/DeleteMark"
    PATH_DELETE = "DocWholeSaleReturn/Delete"
    PATH_LOCK = "DocWholeSaleReturn/Lock"
    PATH_UNLOCK = "DocWholeSaleReturn/Unlock"
    PATH_PERFORM = "DocWholeSaleReturn/Perform"
    PATH_PERFORM_CANCEL = "DocWholeSaleReturn/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocWholeSaleReturnAdd,
        'delete': models.DocWholeSaleReturnDelete,
        'delete_mark': models.DocWholeSaleReturnDeleteMark,
        'edit': models.DocWholeSaleReturnEdit,
        'get': models.DocWholeSaleReturnGet,
        'lock': models.DocWholeSaleReturnLockAndUnlock,
        'perform': models.DocWholeSaleReturnPerformAndCancel,
        'perform_cancel': models.DocWholeSaleReturnPerformAndCancel,
        'unlock': models.DocWholeSaleReturnLockAndUnlock,
    }

    async def get(self, req: models.DocWholeSaleReturnGet | dict[str, Any]) -> models.DocWholeSaleReturnRegosOffsettedArrayResult:
        """POST DocWholeSaleReturn/Get."""
        return await self._call(self.PATH_GET, req, models.DocWholeSaleReturnRegosOffsettedArrayResult)

    async def add(self, req: models.DocWholeSaleReturnAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocWholeSaleReturn/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocWholeSaleReturnEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSaleReturn/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocWholeSaleReturnDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSaleReturn/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocWholeSaleReturnDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSaleReturn/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocWholeSaleReturnLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSaleReturn/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocWholeSaleReturnLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSaleReturn/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.DocWholeSaleReturnPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSaleReturn/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocWholeSaleReturnPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSaleReturn/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocWholeSaleReturnService']
