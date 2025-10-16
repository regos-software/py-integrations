from typing import List, Iterable
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.cheque import DocChequeGetRequest, DocCheque

logger = setup_logger("docs.cheque")


class DocsChequeService:
    PATH_GET = "DocCheque/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocChequeGetRequest) -> List[DocCheque]:
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [DocCheque.model_validate(x) for x in resp.result]

    async def get_by_uuids(self, uuids: Iterable) -> List[DocCheque]:
        return await self.get(DocChequeGetRequest(uuids=list(uuids)))
