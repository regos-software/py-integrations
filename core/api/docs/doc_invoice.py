"""REGOS API service for DocInvoice."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocInvoiceService(RegosAPIService):
    PATH_GET = "DocInvoice/Get"
    PATH_ADD = "DocInvoice/Add"
    PATH_ADD_ON_BASE = "DocInvoice/AddOnBase"
    PATH_EDIT = "DocInvoice/Edit"
    PATH_DELETE_MARK = "DocInvoice/DeleteMark"
    PATH_DELETE = "DocInvoice/Delete"
    PATH_LOCK = "DocInvoice/Lock"
    PATH_UNLOCK = "DocInvoice/Unlock"
    PATH_PERFORM = "DocInvoice/Perform"
    PATH_PERFORM_CANCEL = "DocInvoice/PerformCancel"
    PATH_SEND = "DocInvoice/Send"
    PATH_IMPORT_DOCUMENT_FROM_ROAMING = "DocInvoice/ImportDocumentFromRoaming"
    PATH_SET_STATUS = "DocInvoice/SetStatus"
    PATH_SET_EXTERNAL_DATA = "DocInvoice/SetExternalData"
    PATH_GET_DOCUMENTS_FROM_ROAMING = "DocInvoice/GetDocumentsFromRoaming"
    REQUEST_MODELS = {
        'add': models.DocInvoiceAdd,
        'add_on_base': models.DocInvoiceAddOnBase,
        'delete': models.DocInvoiceDelete,
        'delete_mark': models.DocInvoiceDeleteMark,
        'edit': models.DocInvoiceEdit,
        'get': models.DocInvoiceGet,
        'get_documents_from_roaming': models.DocInvoiceFromRoamingGet,
        'import_document_from_roaming': models.DocInvoiceFromRoamingImport,
        'lock': models.DocInvoiceLockAndUnlock,
        'perform': models.DocInvoicePerformAndCancel,
        'perform_cancel': models.DocInvoicePerformAndCancel,
        'send': models.DocInvoiceSend,
        'set_external_data': models.DocInvoiceSetExternalData,
        'set_status': models.DocInvoiceSetStatus,
        'unlock': models.DocInvoiceLockAndUnlock,
    }

    async def get(self, req: models.DocInvoiceGet | dict[str, Any]) -> models.DocInvoiceRegosOffsettedArrayResult:
        """POST DocInvoice/Get."""
        return await self._call(self.PATH_GET, req, models.DocInvoiceRegosOffsettedArrayResult)

    async def add(self, req: models.DocInvoiceAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocInvoice/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def add_on_base(self, req: models.DocInvoiceAddOnBase | dict[str, Any]) -> models.InsertResult:
        """POST DocInvoice/AddOnBase."""
        return await self._call(self.PATH_ADD_ON_BASE, req, models.InsertResult)

    async def edit(self, req: models.DocInvoiceEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocInvoice/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocInvoiceDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocInvoice/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocInvoiceDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocInvoice/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocInvoiceLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocInvoice/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocInvoiceLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocInvoice/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.DocInvoicePerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocInvoice/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocInvoicePerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocInvoice/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

    async def send(self, req: models.DocInvoiceSend | dict[str, Any]) -> models.SingleObjectResult:
        """POST DocInvoice/Send."""
        return await self._call(self.PATH_SEND, req, models.SingleObjectResult)

    async def import_document_from_roaming(self, req: models.DocInvoiceFromRoamingImport | dict[str, Any]) -> models.SingleObjectResult:
        """POST DocInvoice/ImportDocumentFromRoaming."""
        return await self._call(self.PATH_IMPORT_DOCUMENT_FROM_ROAMING, req, models.SingleObjectResult)

    async def set_status(self, req: models.DocInvoiceSetStatus | dict[str, Any]) -> models.SingleObjectResult:
        """POST DocInvoice/SetStatus."""
        return await self._call(self.PATH_SET_STATUS, req, models.SingleObjectResult)

    async def set_external_data(self, req: models.DocInvoiceSetExternalData | dict[str, Any]) -> models.SingleObjectResult:
        """POST DocInvoice/SetExternalData."""
        return await self._call(self.PATH_SET_EXTERNAL_DATA, req, models.SingleObjectResult)

    async def get_documents_from_roaming(self, req: models.DocInvoiceFromRoamingGet | dict[str, Any]) -> models.DocInvoiceFromRoamingRegosOffsettedArrayResult:
        """POST DocInvoice/GetDocumentsFromRoaming."""
        return await self._call(self.PATH_GET_DOCUMENTS_FROM_ROAMING, req, models.DocInvoiceFromRoamingRegosOffsettedArrayResult)

__all__ = ['DocInvoiceService']
