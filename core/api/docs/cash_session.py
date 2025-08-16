from typing import List, Iterable
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.cash_session import DocCashSessionGetRequest, DocCashSession

logger = setup_logger("docs.CashSession")

class DocCashSessionService:
    PATH_GET = "DocCashSession/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocCashSessionGetRequest) -> List[DocCashSession]:
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [DocCashSession.model_validate(x) for x in resp.result]

    async def get_by_uuids(self, uuids: Iterable) -> List[DocCashSession]:
        return await self.get(DocCashSessionGetRequest(uuids=list(uuids)))
