"""REGOS API service for DocSetPrice."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocSetPriceService(RegosAPIService):
    PATH_GET = "DocSetPrice/get"
    PATH_ADD = "DocSetPrice/add"
    PATH_EDIT = "DocSetPrice/edit"
    PATH_DELETE_MARK = "DocSetPrice/deleteMark"
    PATH_DELETE = "DocSetPrice/delete"
    PATH_LOCK = "DocSetPrice/lock"
    PATH_UNLOCK = "DocSetPrice/Unlock"
    PATH_PERFORM = "DocSetPrice/perform"
    PATH_PERFORM_CANCEL = "DocSetPrice/performCancel"
    REQUEST_MODELS = {
        'add': models.DocSetPriceAdd,
        'delete': models.DocSetPriceDelete,
        'delete_mark': models.DocSetPriceDeleteMark,
        'edit': models.DocSetPriceEdit,
        'get': models.DocSetPriceGet,
        'lock': models.DocSetPriceLockAndUnlock,
        'perform': models.DocSetPricePerformAndCancel,
        'perform_cancel': models.DocSetPricePerformAndCancel,
        'unlock': models.DocSetPriceLockAndUnlock,
    }

    async def get(self, req: models.DocSetPriceGet | dict[str, Any]) -> models.DocSetPriceRegosOffsettedArrayResult:
        """POST DocSetPrice/get."""
        return await self._call(self.PATH_GET, req, models.DocSetPriceRegosOffsettedArrayResult)

    async def add(self, req: models.DocSetPriceAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocSetPrice/add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocSetPriceEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocSetPrice/edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocSetPriceDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocSetPrice/deleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocSetPriceDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocSetPrice/delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocSetPriceLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocSetPrice/lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocSetPriceLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocSetPrice/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.DocSetPricePerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocSetPrice/perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocSetPricePerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocSetPrice/performCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocSetPriceService']
