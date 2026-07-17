"""REGOS API service for DocPayment."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocPaymentService(RegosAPIService):
    PATH_GET = "DocPayment/Get"
    PATH_ADD = "DocPayment/Add"
    PATH_EDIT = "DocPayment/Edit"
    PATH_DELETE_MARK = "DocPayment/DeleteMark"
    PATH_DELETE = "DocPayment/Delete"
    PATH_PERFORM = "DocPayment/Perform"
    PATH_PERFORM_CANCEL = "DocPayment/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocPaymentAdd,
        'delete': models.DocPaymentDelete,
        'delete_mark': models.DocPaymentDeleteMark,
        'edit': models.DocPaymentEdit,
        'get': models.DocPaymentGet,
        'perform': models.DocPaymentPerformAndCancel,
        'perform_cancel': models.DocPaymentPerformAndCancel,
    }

    async def get(self, req: models.DocPaymentGet | dict[str, Any]) -> models.DocPaymentRegosOffsettedArrayResult:
        """POST DocPayment/Get."""
        return await self._call(self.PATH_GET, req, models.DocPaymentRegosOffsettedArrayResult)

    async def add(self, req: models.DocPaymentAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocPayment/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocPaymentEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocPayment/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocPaymentDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocPayment/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocPaymentDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocPayment/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def perform(self, req: models.DocPaymentPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocPayment/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocPaymentPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocPayment/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocPaymentService']
