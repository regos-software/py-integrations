from typing import List
from pydantic import TypeAdapter

from schemas.api.base import APIBaseResponse, ArrayResult
from schemas.api.docs.purchase_operation import (
    PurchaseOperation,
    PurchaseOperationGetRequest,
    PurchaseOperationAddRequest,
    PurchaseOperationEditItem,
    PurchaseOperationDeleteItem,
)


class PurchaseOperationService:
    PATH_GET = "PurchaseOperation/Get"
    PATH_ADD = "PurchaseOperation/Add"
    PATH_EDIT = "PurchaseOperation/Edit"
    PATH_DELETE = "PurchaseOperation/Delete"

    def __init__(self, api):
        self.api = api

    async def get_raw(self, req: PurchaseOperationGetRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    async def get_by_document_id(self, doc_id: int) -> List[PurchaseOperation]:
        return await self.get_raw(PurchaseOperationGetRequest(document_ids=[doc_id]))

    async def add_raw(self, req: List[PurchaseOperationAddRequest]) -> APIBaseResponse:
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse)

    async def edit_raw(self, req: List[PurchaseOperationEditItem]) -> APIBaseResponse:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse)

    async def delete_raw(
        self, req: List[PurchaseOperationDeleteItem]
    ) -> APIBaseResponse:
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse)
