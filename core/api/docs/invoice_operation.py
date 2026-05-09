from __future__ import annotations

from core.logger import setup_logger
from schemas.api.docs.invoice_operation import (
    InvoiceOperationAddRequest,
    InvoiceOperationAddResponse,
    InvoiceOperationGetRequest,
    InvoiceOperationGetResponse,
)

logger = setup_logger("docs.InvoiceOperation")


class InvoiceOperationService:
    """Service for InvoiceOperation endpoints."""

    PATH_GET = "InvoiceOperation/Get"
    PATH_ADD = "InvoiceOperation/Add"

    def __init__(self, api):
        self.api = api

    async def get(self, req: InvoiceOperationGetRequest) -> InvoiceOperationGetResponse:
        return await self.api.call(self.PATH_GET, req, InvoiceOperationGetResponse)

    async def add(self, req: InvoiceOperationAddRequest) -> InvoiceOperationAddResponse:
        return await self.api.call(self.PATH_ADD, req, InvoiceOperationAddResponse)
