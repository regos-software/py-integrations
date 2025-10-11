from typing import List, Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, APIErrorResult, IDRequest
from schemas.api.docs.wholesale import (
    DocWholeSaleGetRequest,
    DocWholeSale,
    DocWholeSaleGetResponse,
)

logger = setup_logger("docs.WholeSale")


class DocWholeSaleService:
    PATH_GET = "DocWholeSale/Get"
    PATH_PERFORM = "DocWholeSale/Perform"
    PATH_PERFORM_CANCEL = "DocWholeSale/PerformCancel"
    PATH_LOCK = "DocWholeSale/Lock"
    PATH_UNLOCK = "DocWholeSale/Unlock"

    def __init__(self, api):
        self.api = api

    async def get_raw(self, req: DocWholeSaleGetRequest) -> DocWholeSaleGetResponse:
        """ """
        return await self.api.call(self.PATH_GET, req, DocWholeSaleGetResponse)

    async def perform_raw(self, req: IDRequest) -> APIBaseResponse:
        """ """
        return await self.api.call(self.PATH_PERFORM, req, APIBaseResponse)

    async def perform_cancel_raw(self, req: IDRequest) -> APIBaseResponse:
        """ """
        return await self.api.call(self.PATH_PERFORM_CANCEL, req, APIBaseResponse)

    async def lock_raw(self, req: IDRequest) -> APIBaseResponse:
        """ """
        return await self.api.call(self.PATH_LOCK, req, APIBaseResponse)

    async def unlock_raw(self, req: IDRequest) -> APIBaseResponse:
        """ """
        return await self.api.call(self.PATH_UNLOCK, req, APIBaseResponse)

    async def get_by_id(self, id_: int) -> Optional[DocWholeSale]:
        """
        Получить один документ по ID. Возвращает None, если не найден.
        """
        resp = await self.get_raw(DocWholeSaleGetRequest(ids=[id_]))
        return resp.result[0] if len(resp.result) >= 1 else None
