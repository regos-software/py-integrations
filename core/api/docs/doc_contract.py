from __future__ import annotations

from typing import Optional

from core.logger import setup_logger
from schemas.api.docs.doc_contract import (
    DocContract,
    DocContractAddRequest,
    DocContractAddResponse,
    DocContractGetRequest,
    DocContractGetResponse,
    DocContractGetShortResponse,
    DocContractShort,
)

logger = setup_logger("docs.DocContract")


class DocContractService:
    """Service for DocContract endpoints."""

    PATH_GET = "DocContract/Get"
    PATH_GET_SHORT = "DocContract/GetShort"
    PATH_ADD = "DocContract/Add"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocContractGetRequest) -> DocContractGetResponse:
        return await self.api.call(self.PATH_GET, req, DocContractGetResponse)

    async def get_short(self, req: DocContractGetRequest) -> DocContractGetShortResponse:
        return await self.api.call(self.PATH_GET_SHORT, req, DocContractGetShortResponse)

    async def add(self, req: DocContractAddRequest) -> DocContractAddResponse:
        return await self.api.call(self.PATH_ADD, req, DocContractAddResponse)

    async def get_by_id(self, id_: int) -> Optional[DocContract]:
        resp = await self.get(DocContractGetRequest(ids=[id_], limit=1))
        result = resp.result or []
        return result[0] if result else None

    async def get_short_by_id(self, id_: int) -> Optional[DocContractShort]:
        resp = await self.get_short(DocContractGetRequest(ids=[id_], limit=1))
        result = resp.result or []
        return result[0] if result else None
