from typing import List
from pydantic import TypeAdapter

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

    def __init__(self, api):
        self.api = api

    async def get_raw(self, req: WholeSaleOperationGetRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    async def get_by_document_id(self, doc_id: int) -> List[WholeSaleOperation]:
        return await self.get_raw(WholeSaleOperationGetRequest(document_ids=[doc_id]))

    async def add_raw(self, req: List[WholeSaleOperationAddRequest]) -> APIBaseResponse:
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse)

    async def edit_raw(self, req: List[WholeSaleOperationEditItem]) -> APIBaseResponse:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse)

    async def delete_raw(
        self, req: List[WholeSaleOperationDeleteItem]
    ) -> APIBaseResponse:
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse)
