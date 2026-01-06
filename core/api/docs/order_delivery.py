from typing import Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.order_delivery import (
    DocOrderDelivery,
    DocOrderDeliveryAddFullRequest,
    DocOrderDeliveryGetRequest,
    DocOrderDeliveryGetResponse,
)

logger = setup_logger("docs.OrderDelivery")


class DocOrderDeliveryService:
    PATH_GET = "DocOrderDelivery/Get"
    PATH_GET_POS = "POS/DocOrderDelivery/Get"
    PATH_ADD_FULL = "DocOrderDelivery/AddFull"

    def __init__(self, api):
        self.api = api

    async def get(
        self,
        req: DocOrderDeliveryGetRequest,
        *,
        use_pos: bool = False,
    ) -> DocOrderDeliveryGetResponse:
        """Получить документы розничных заказов."""
        path = self.PATH_GET_POS if use_pos else self.PATH_GET
        return await self.api.call(path, req, DocOrderDeliveryGetResponse)

    async def get_by_id(
        self,
        doc_id: int,
        *,
        use_pos: bool = False,
    ) -> Optional[DocOrderDelivery]:
        """Получить документ розничного заказа по ID."""
        resp = await self.get(DocOrderDeliveryGetRequest(ids=[doc_id]), use_pos=use_pos)
        return resp.result[0] if resp.result else None

    async def add_full(self, req: DocOrderDeliveryAddFullRequest) -> APIBaseResponse:
        """Создать заполненный документ розничного заказа."""
        return await self.api.call(self.PATH_ADD_FULL, req, APIBaseResponse)
