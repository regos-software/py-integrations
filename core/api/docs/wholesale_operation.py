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
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return APIBaseResponse(ok=False, result=[])
        return resp

    async def get_by_document_id(self, doc_id: int) -> List[WholeSaleOperation]:
        resp = await self.get_raw(WholeSaleOperationGetRequest(document_ids=[doc_id]))
        return resp.result if resp.ok else []

    async def add_raw(self, req: List[WholeSaleOperationAddRequest]) -> APIBaseResponse:
        resp = await self.api.call(self.PATH_ADD, req, APIBaseResponse)
        return resp

    async def edit_raw(self, req: List[WholeSaleOperationEditItem]) -> APIBaseResponse:
        resp = await self.api.call(self.PATH_EDIT, req, APIBaseResponse)
        return resp

    async def delete_raw(
        self, req: List[WholeSaleOperationDeleteItem]
    ) -> APIBaseResponse:
        resp = await self.api.call(self.PATH_DELETE, req, APIBaseResponse)
        return resp
