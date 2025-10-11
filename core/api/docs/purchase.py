from typing import List, Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, APIErrorResult
from schemas.api.docs.purchase import (
    DocPurchaseGetRequest,
    DocPurchase,
    DocPurchaseGetResponse,
)

logger = setup_logger("docs.Purchase")


class DocPurchaseService:
    PATH_GET = "DocPurchase/Get"

    def __init__(self, api):
        self.api = api

    async def get_raw(self, req: DocPurchaseGetRequest) -> DocPurchaseGetResponse:
        """ """
        return await self.api.call(self.PATH_GET, req, DocPurchaseGetResponse)

    async def get_by_id(self, id_: int) -> Optional[DocPurchase]:
        """
        Получить один документ по ID. Возвращает None, если не найден.
        """
        resp = await self.get_raw(DocPurchaseGetRequest(ids=[id_]))
        return resp.result[0] if len(resp.result) >= 1 else None
