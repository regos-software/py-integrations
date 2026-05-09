from __future__ import annotations

from typing import Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, ArrayResult, IDRequest
from schemas.api.docs.doc_invoice import (
    DocInvoice,
    DocInvoiceActionResponse,
    DocInvoiceAddRequest,
    DocInvoiceAddResponse,
    DocInvoiceGetRequest,
    DocInvoiceGetResponse,
    DocInvoiceSetExternalDataRequest,
    DocInvoiceSetStatusRequest,
)

logger = setup_logger("docs.DocInvoice")


class DocInvoiceService:
    """Service for DocInvoice endpoints."""

    PATH_GET = "DocInvoice/Get"
    PATH_ADD = "DocInvoice/Add"
    PATH_SET_STATUS = "DocInvoice/SetStatus"
    PATH_SET_EXTERNAL_DATA = "DocInvoice/SetExternalData"
    PATH_LOCK = "DocInvoice/Lock"
    PATH_UNLOCK = "DocInvoice/Unlock"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocInvoiceGetRequest) -> DocInvoiceGetResponse:
        return await self.api.call(self.PATH_GET, req, DocInvoiceGetResponse)

    async def add(self, req: DocInvoiceAddRequest) -> DocInvoiceAddResponse:
        return await self.api.call(self.PATH_ADD, req, DocInvoiceAddResponse)

    async def set_status(self, req: DocInvoiceSetStatusRequest) -> DocInvoiceActionResponse:
        return await self.api.call(self.PATH_SET_STATUS, req, DocInvoiceActionResponse)

    async def set_external_data(
        self, req: DocInvoiceSetExternalDataRequest
    ) -> DocInvoiceActionResponse:
        return await self.api.call(self.PATH_SET_EXTERNAL_DATA, req, DocInvoiceActionResponse)

    async def lock(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_LOCK, req, APIBaseResponse[ArrayResult])

    async def unlock(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_UNLOCK, req, APIBaseResponse[ArrayResult])

    async def get_by_id(self, id_: int) -> Optional[DocInvoice]:
        resp = await self.get(DocInvoiceGetRequest(ids=[id_], limit=1))
        result = resp.result or []
        return result[0] if result else None
