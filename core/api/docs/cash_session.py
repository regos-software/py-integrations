from typing import List, Iterable
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.cash_session import DocCashSessionGetRequest, DocCashSession

logger = setup_logger("docs.CashSession")


class DocCashSessionService:
    PATH_GET = "DocCashSession/Get"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: DocCashSessionGetRequest
    ) -> APIBaseResponse[List[DocCashSession]]:
        resp = await self.api.call(
            self.PATH_GET, req, APIBaseResponse[List[DocCashSession]]
        )
        return resp

    async def get_by_uuids(
        self, uuids: List[str] | Iterable[str]
    ) -> APIBaseResponse[List[DocCashSession]]:
        return await self.get(DocCashSessionGetRequest(uuids=list(uuids)))
