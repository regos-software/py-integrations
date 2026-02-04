from typing import List, Iterable
from core.logger import setup_logger
from schemas.api.docs.cash_session import (
    DocCashSession,
    DocCashSessionGetRequest,
    DocCashSessionGetResponse,
)

logger = setup_logger("docs.CashSession")


class DocCashSessionService:
    PATH_GET = "DocCashSession/Get"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: DocCashSessionGetRequest
    ) -> DocCashSessionGetResponse:
        payload = req.model_dump(mode="json", exclude_none=True)
        resp = await self.api.call(
            self.PATH_GET, payload, DocCashSessionGetResponse
        )
        return resp

    async def get_by_uuids(
        self, uuids: List[str] | Iterable[str]
    ) -> DocCashSessionGetResponse:
        return await self.get(DocCashSessionGetRequest(uuids=list(uuids)))
