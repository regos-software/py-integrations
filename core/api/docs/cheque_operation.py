from typing import List, Iterable
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.cheque_operation import (
    DocChequeOperationGetRequest,
    DocChequeOperation,
)

logger = setup_logger("docs.ChequeOperation")


class DocChequeOperationService:
    PATH_GET = "DocChequeOperation/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocChequeOperationGetRequest) -> List[DocChequeOperation]:
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [DocChequeOperation.model_validate(x) for x in resp.result]

    async def get_by_uuids(self, uuids: Iterable) -> List[DocChequeOperation]:
        return await self.get(DocChequeOperationGetRequest(uuids=list(uuids)))

    async def get_by_doc_sale_uuid(
        self, doc_sale_uuid: str
    ) -> List[DocChequeOperation]:
        return await self.get(DocChequeOperationGetRequest(doc_sale_uuid=doc_sale_uuid))
