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

    async def _get(self, req: DocPurchaseGetRequest) -> DocPurchaseGetResponse:
        resp = await self.api.call(self.PATH_GET, req, DocPurchaseGetResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning(
                "DocPurchase/Get non-ok or non-list result: %s",
                getattr(resp, "result", None),
            )
            return DocPurchaseGetResponse(
                ok=False, result=APIErrorResult(getattr(resp, "result", None))
            )
        return resp

    async def get(self, req: DocPurchaseGetRequest) -> DocPurchaseGetResponse:
        """
        Вызов /v1/DocPurchase/Get с любыми фильтрами из DocPurchaseGetRequest.
        Возвращает список DocPurchase.
        """
        resp = await self._get(req)
        return resp

    async def get_by_id(self, id_: int) -> Optional[DocPurchase]:
        """
        Получить один документ по ID. Возвращает None, если не найден.
        """
        resp = await self.get(DocPurchaseGetRequest(ids=[id_]))
        return resp.result[0] if len(resp.result) >= 1 else None
