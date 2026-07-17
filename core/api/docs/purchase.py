from typing import Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, ArrayResult, IDRequest
from schemas.api.docs.purchase import (
    DocPurchaseAddRequest,
    DocPurchaseGetRequest,
    DocPurchase,
    DocPurchaseGetResponse,
)

logger = setup_logger("docs.Purchase")


class DocPurchaseService:
    PATH_GET = "DocPurchase/Get"
    PATH_PERFORM = "DocPurchase/Perform"
    PATH_ADD = "DocPurchase/Add"
    PATH_PERFORM_CANCEL = "DocPurchase/PerformCancel"
    PATH_LOCK = "DocPurchase/Lock"
    PATH_UNLOCK = "DocPurchase/Unlock"
    PATH_DELETE_MARK = "DocPurchase/DeleteMark"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocPurchaseGetRequest) -> DocPurchaseGetResponse:
        """ """
        return await self.api.call(self.PATH_GET, req, DocPurchaseGetResponse)

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

    async def add(self, req: DocPurchaseAddRequest) -> APIBaseResponse:
        """Добавить документ поступления."""
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse)

    async def get_by_id(self, id_: int) -> Optional[DocPurchase]:
        """
        Получить один документ по ID. Возвращает None, если не найден.
        """
        resp = await self.get(DocPurchaseGetRequest(ids=[id_]))
        return resp.result[0] if len(resp.result) >= 1 else None

    async def delete_mark(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """ """
        return await self.api.call(
            self.PATH_DELETE_MARK, req, APIBaseResponse[ArrayResult]
        )
