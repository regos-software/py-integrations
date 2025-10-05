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
    PATH_GET    = "PurchaseOperation/Get"
    PATH_ADD    = "PurchaseOperation/Add"
    PATH_EDIT   = "PurchaseOperation/Edit"
    PATH_DELETE = "PurchaseOperation/Delete"

    def __init__(self, api):
        self.api = api

    async def get(self, req: PurchaseOperationGetRequest) -> List[PurchaseOperation]:
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        ta = TypeAdapter(List[PurchaseOperation])
        return ta.validate_python(resp.result)

    async def get_by_document_id(self, doc_id: int) -> List[PurchaseOperation]:
        return await self.get(PurchaseOperationGetRequest(document_ids=[doc_id]))

    async def add(self, items: List[PurchaseOperationAddRequest]) -> ArrayResult:
        # передаём список моделей как есть — RegosAPI.call сам сериализует
        resp = await self.api.call(self.PATH_ADD, items, APIBaseResponse)
        return ArrayResult.model_validate(resp.result or {})

    async def edit(self, items: List[PurchaseOperationEditItem]) -> ArrayResult:
        resp = await self.api.call(self.PATH_EDIT, items, APIBaseResponse)
        return ArrayResult.model_validate(resp.result or {})

    async def delete(self, items: List[PurchaseOperationDeleteItem]) -> ArrayResult:
        resp = await self.api.call(self.PATH_DELETE, items, APIBaseResponse)
        return ArrayResult.model_validate(resp.result or {})
