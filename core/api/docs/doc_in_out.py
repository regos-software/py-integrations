"""REGOS API service for DocInOut."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocInOutService(RegosAPIService):
    PATH_GET = "DocInOut/Get"
    PATH_ADD = "DocInOut/Add"
    PATH_EDIT = "DocInOut/Edit"
    PATH_DELETE_MARK = "DocInOut/DeleteMark"
    PATH_DELETE = "DocInOut/Delete"
    PATH_LOCK = "DocInOut/Lock"
    PATH_UNLOCK = "DocInOut/Unlock"
    PATH_PERFORM = "DocInOut/Perform"
    PATH_PERFORM_CANCEL = "DocInOut/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocInOutAdd,
        'delete': models.DocInOutDelete,
        'delete_mark': models.DocInOutDeleteMark,
        'edit': models.DocInOutEdit,
        'get': models.DocInOutGet,
        'lock': models.DocInOutLockAndUnlock,
        'perform': models.DocInOutPerformAndCancel,
        'perform_cancel': models.DocInOutPerformAndCancel,
        'unlock': models.DocInOutLockAndUnlock,
    }

    async def get(self, req: models.DocInOutGet | dict[str, Any]) -> models.DocInOutRegosOffsettedArrayResult:
        """POST DocInOut/Get."""
        return await self._call(self.PATH_GET, req, models.DocInOutRegosOffsettedArrayResult)

    async def add(self, req: models.DocInOutAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocInOut/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocInOutEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocInOut/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocInOutDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocInOut/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocInOutDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocInOut/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocInOutLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocInOut/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocInOutLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocInOut/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.DocInOutPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocInOut/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocInOutPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocInOut/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocInOutService']
