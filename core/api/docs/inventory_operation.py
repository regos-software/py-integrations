from typing import List

from schemas.api.base import APIBaseResponse, ArrayResult
from schemas.api.docs.inventory_operation import (
    InventoryOperation,
    InventoryOperationAddRequest,
    InventoryOperationDeleteItem,
    InventoryOperationEditItem,
    InventoryOperationGetRequest,
)


class InventoryOperationService:
    PATH_GET = "InventoryOperation/Get"
    PATH_ADD = "InventoryOperation/Add"
    PATH_EDIT = "InventoryOperation/Edit"
    PATH_DELETE = "InventoryOperation/Delete"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: InventoryOperationGetRequest
    ) -> APIBaseResponse[List[InventoryOperation]]:
        return await self.api.call(
            self.PATH_GET, req, APIBaseResponse[List[InventoryOperation]]
        )

    async def get_by_document_id(self, doc_id: int) -> List[InventoryOperation]:
        resp = await self.get(InventoryOperationGetRequest(document_ids=[doc_id]))
        return resp.result

    async def add(
        self, req: List[InventoryOperationAddRequest]
    ) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse[ArrayResult])

    async def edit(
        self, req: List[InventoryOperationEditItem]
    ) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse[ArrayResult])

    async def delete(
        self, req: List[InventoryOperationDeleteItem]
    ) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse[ArrayResult])
