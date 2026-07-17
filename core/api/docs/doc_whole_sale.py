"""REGOS API service for DocWholeSale."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocWholeSaleService(RegosAPIService):
    PATH_GET = "DocWholeSale/Get"
    PATH_ADD = "DocWholeSale/Add"
    PATH_EDIT = "DocWholeSale/Edit"
    PATH_DELETE_MARK = "DocWholeSale/DeleteMark"
    PATH_DELETE = "DocWholeSale/Delete"
    PATH_LOCK = "DocWholeSale/Lock"
    PATH_UNLOCK = "DocWholeSale/Unlock"
    PATH_PERFORM = "DocWholeSale/Perform"
    PATH_PERFORM_CANCEL = "DocWholeSale/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocWholeSaleAdd,
        'delete': models.DocWholeSaleDelete,
        'delete_mark': models.DocWholeSaleDeleteMark,
        'edit': models.DocWholeSaleEdit,
        'get': models.DocWholeSaleGet,
        'lock': models.DocWholeSaleLockAndUnlock,
        'perform': models.DocWholeSalePerformAndCancel,
        'perform_cancel': models.DocWholeSalePerformAndCancel,
        'unlock': models.DocWholeSaleLockAndUnlock,
    }

    async def get(self, req: models.DocWholeSaleGet | dict[str, Any]) -> models.DocWholeSaleRegosOffsettedArrayResult:
        """POST DocWholeSale/Get."""
        return await self._call(self.PATH_GET, req, models.DocWholeSaleRegosOffsettedArrayResult)

    async def add(self, req: models.DocWholeSaleAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocWholeSale/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocWholeSaleEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSale/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocWholeSaleDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSale/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocWholeSaleDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSale/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocWholeSaleLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSale/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocWholeSaleLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSale/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.DocWholeSalePerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSale/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocWholeSalePerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocWholeSale/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocWholeSaleService']
