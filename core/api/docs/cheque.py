from typing import List, Iterable
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.cheque import DocChequeGetRequest, DocCheque

logger = setup_logger("docs.cheque")


class DocsChequeService:
    PATH_GET = "DocCheque/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocChequeGetRequest) -> APIBaseResponse[List[DocCheque]]:
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        return resp

    async def get_by_uuids(self, uuids: Iterable) -> APIBaseResponse[List[DocCheque]]:
        return await self.get(DocChequeGetRequest(uuids=list(uuids)))
