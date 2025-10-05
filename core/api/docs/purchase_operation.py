from typing import List, Iterable
from pydantic import TypeAdapter

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.purchase_operation import (
    PurchaseOperationGetRequest,
    PurchaseOperation,
    PurchaseOperationAddRequest,
    PurchaseOperationEditItem,
    PurchaseOperationDeleteItem,
    ArrayResult,
)

logger = setup_logger("docs.PurchaseOperation")


class PurchaseOperationService:
    PATH_GET = "PurchaseOperation/Get"
    PATH_ADD = "PurchaseOperation/Add"
    PATH_EDIT = "PurchaseOperation/Edit"
    PATH_DELETE = "PurchaseOperation/Delete"

    def __init__(self, api):
        self.api = api

    # -------- Get --------
    async def get(self, req: PurchaseOperationGetRequest) -> List[PurchaseOperation]:
        resp = await self.api.call(selfPATH_GET := self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        ta = TypeAdapter(List[PurchaseOperation])
        return ta.validate_python(resp.result)

    async def get_by_document_id(self, document_id: int) -> List[PurchaseOperation]:
        return await self.get(PurchaseOperationGetRequest(document_ids=[document_id]))

    async def get_by_ids(self, ids: Iterable[int]) -> List[PurchaseOperation]:
        return await self.get(PurchaseOperationGetRequest(ids=list(ids)))

    # -------- Add/Edit/Delete --------
    async def add(self, items: List[PurchaseOperationAddRequest]) -> ArrayResult:
        # /v1/PurchaseOperation/Add принимает МАССИВ элементов
        resp = await self.api.call(self.PATH_ADD, items, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, dict):
            return ArrayResult(row_affected=0, ids=[])
        return ArrayResult.model_validate(resp.result)

    async def edit(self, items: List[PurchaseOperationEditItem]) -> ArrayResult:
        resp = await self.api.call(self.PATH_EDIT, items, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, dict):
            return ArrayResult(row_affected=0, ids=[])
        return ArrayResult.model_validate(resp.result)

    async def delete(self, items: List[PurchaseOperationDeleteItem]) -> ArrayResult:
        resp = await self.api.call(self.PATH_DELETE, items, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, dict):
            return ArrayResult(row_affected=0, ids=[])
        return ArrayResult.model_validate(resp.result)
