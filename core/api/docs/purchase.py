from typing import List, Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.purchase import DocPurchaseGetRequest, DocPurchase

logger = setup_logger("docs.Purchase")


class DocPurchaseService:
    PATH_GET = "DocPurchase/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocPurchaseGetRequest) -> List[DocPurchase]:
        """
        Вызов /v1/DocPurchase/Get с любыми фильтрами из DocPurchaseGetRequest.
        Возвращает список DocPurchase.
        """
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning("DocPurchase/Get non-ok or non-list result: %s", getattr(resp, "result", None))
            return []
        return [DocPurchase.model_validate(x) for x in resp.result]

    async def get_by_id(self, id_: int) -> Optional[DocPurchase]:
        """
        Получить один документ по ID. Возвращает None, если не найден.
        """
        items = await self.get(DocPurchaseGetRequest(ids=[id_]))
        return items[0] if items else None
