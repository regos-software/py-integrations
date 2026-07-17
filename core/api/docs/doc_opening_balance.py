"""REGOS API service for DocOpeningBalance."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocOpeningBalanceService(RegosAPIService):
    PATH_GET = "DocOpeningBalance/Get"
    PATH_ADD = "DocOpeningBalance/Add"
    PATH_EDIT = "DocOpeningBalance/Edit"
    PATH_DELETE_MARK = "DocOpeningBalance/DeleteMark"
    PATH_DELETE = "DocOpeningBalance/Delete"
    PATH_PERFORM = "DocOpeningBalance/Perform"
    PATH_PERFORM_CANCEL = "DocOpeningBalance/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocOpeningBalanceAdd,
        'delete': models.DocOpeningBalanceDelete,
        'delete_mark': models.DocOpeningBalanceDeleteMark,
        'edit': models.DocOpeningBalanceEdit,
        'get': models.DocOpeningBalanceGet,
        'perform': models.DocOpeningBalancePerformAndCancel,
        'perform_cancel': models.DocOpeningBalancePerformAndCancel,
    }

    async def get(self, req: models.DocOpeningBalanceGet | dict[str, Any]) -> models.DocOpeningBalanceRegosOffsettedArrayResult:
        """POST DocOpeningBalance/Get."""
        return await self._call(self.PATH_GET, req, models.DocOpeningBalanceRegosOffsettedArrayResult)

    async def add(self, req: models.DocOpeningBalanceAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocOpeningBalance/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocOpeningBalanceEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocOpeningBalance/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocOpeningBalanceDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocOpeningBalance/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocOpeningBalanceDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocOpeningBalance/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def perform(self, req: models.DocOpeningBalancePerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocOpeningBalance/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocOpeningBalancePerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocOpeningBalance/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocOpeningBalanceService']
