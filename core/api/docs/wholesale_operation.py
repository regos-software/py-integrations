from typing import List

from core.api.regos_api import RegosAPI
from schemas.api.base import APIBaseResponse, ArrayResult
from schemas.api.docs.wholesale_operation import (
    WholeSaleOperation,
    WholeSaleOperationGetRequest,
    WholeSaleOperationAddRequest,
    WholeSaleOperationEditItem,
    WholeSaleOperationDeleteItem,
)


class WholeSaleOperationService:
    PATH_GET = "WholeSaleOperation/Get"
    PATH_ADD = "WholeSaleOperation/Add"
    PATH_EDIT = "WholeSaleOperation/Edit"
    PATH_DELETE = "WholeSaleOperation/Delete"

    def __init__(self, api: RegosAPI):
        self.api = api

    async def get(
        self, req: WholeSaleOperationGetRequest
    ) -> APIBaseResponse[List[WholeSaleOperation]]:
        return await self.api.call(
            self.PATH_GET, req, APIBaseResponse[List[WholeSaleOperation]]
        )

    async def get_by_document_id(
        self, doc_id: int
    ) -> APIBaseResponse[List[WholeSaleOperation]]:
        return await self.get(WholeSaleOperationGetRequest(document_ids=[doc_id]))

    async def add(
        self, req: List[WholeSaleOperationAddRequest]
    ) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse[ArrayResult])

    async def edit(
        self, req: List[WholeSaleOperationEditItem]
    ) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse[ArrayResult])

    async def delete(
        self, req: List[WholeSaleOperationDeleteItem]
    ) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse[ArrayResult])
