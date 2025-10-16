from typing import List, Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, ArrayResult, IDRequest
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
    PATH_DELETE_MARK = "DocWholeSale/DeleteMark"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: DocWholeSaleGetRequest
    ) -> APIBaseResponse[List[DocWholeSale]]:
        """ """
        return await self.api.call(
            self.PATH_GET, req, APIBaseResponse[List[DocWholeSale]]
        )

    async def perform(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """ """
        return await self.api.call(self.PATH_PERFORM, req, APIBaseResponse[ArrayResult])

    async def perform_cancel(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """ """
        return await self.api.call(
            self.PATH_PERFORM_CANCEL, req, APIBaseResponse[ArrayResult]
        )

    async def lock(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """ """
        return await self.api.call(self.PATH_LOCK, req, APIBaseResponse[ArrayResult])

    async def unlock(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """ """
        return await self.api.call(self.PATH_UNLOCK, req, APIBaseResponse[ArrayResult])

    async def get_by_id(self, id_: int) -> Optional[DocWholeSale]:
        """
        Получить один документ по ID. Возвращает None, если не найден.
        """
        resp = await self.get(DocWholeSaleGetRequest(ids=[id_]))
        return resp.result[0] if len(resp.result) >= 1 else None

    async def delete_mark(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """ """
        return await self.api.call(
            self.PATH_DELETE_MARK, req, APIBaseResponse[ArrayResult]
        )
