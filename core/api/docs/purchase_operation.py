from typing import List

from core.api.regos_api import RegosAPI
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

    def __init__(self, api: RegosAPI):
        self.api = api

    async def get(
        self, req: PurchaseOperationGetRequest
    ) -> APIBaseResponse[List[PurchaseOperation]]:
        return await self.api.call(
            self.PATH_GET, req, APIBaseResponse[List[PurchaseOperation]]
        )

    async def get_by_document_id(self, doc_id: int) -> List[PurchaseOperation]:
        return await self.get(PurchaseOperationGetRequest(document_ids=[doc_id]))

    async def add(
        self, req: List[PurchaseOperationAddRequest]
    ) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse[ArrayResult])

    async def edit(
        self, req: List[PurchaseOperationEditItem]
    ) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse[ArrayResult])

    async def delete(
        self, req: List[PurchaseOperationDeleteItem]
    ) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse[ArrayResult])
