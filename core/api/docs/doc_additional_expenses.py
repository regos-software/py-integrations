"""REGOS API service for DocAdditionalExpenses."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocAdditionalExpensesService(RegosAPIService):
    PATH_GET = "DocAdditionalExpenses/Get"
    PATH_ADD = "DocAdditionalExpenses/Add"
    PATH_EDIT = "DocAdditionalExpenses/Edit"
    PATH_DELETE_MARK = "DocAdditionalExpenses/DeleteMark"
    PATH_DELETE = "DocAdditionalExpenses/Delete"
    PATH_LOCK = "DocAdditionalExpenses/Lock"
    PATH_UNLOCK = "DocAdditionalExpenses/Unlock"
    PATH_PERFORM = "DocAdditionalExpenses/Perform"
    PATH_PERFORM_CANCEL = "DocAdditionalExpenses/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocAdditionalExpensesAdd,
        'delete': models.Base_ID,
        'delete_mark': models.Base_ID,
        'edit': models.DocAdditionalExpensesEdit,
        'get': models.DocAdditionalExpensesGet,
        'lock': models.BaseLockAndUnlock,
        'perform': models.Base_ID,
        'perform_cancel': models.Base_ID,
        'unlock': models.BaseLockAndUnlock,
    }

    async def get(self, req: models.DocAdditionalExpensesGet | dict[str, Any]) -> models.DocAdditionalExpensesRegosOffsettedArrayResult:
        """POST DocAdditionalExpenses/Get."""
        return await self._call(self.PATH_GET, req, models.DocAdditionalExpensesRegosOffsettedArrayResult)

    async def add(self, req: models.DocAdditionalExpensesAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocAdditionalExpenses/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocAdditionalExpensesEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocAdditionalExpenses/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocAdditionalExpenses/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocAdditionalExpenses/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.BaseLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocAdditionalExpenses/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.BaseLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocAdditionalExpenses/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocAdditionalExpenses/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST DocAdditionalExpenses/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocAdditionalExpensesService']
