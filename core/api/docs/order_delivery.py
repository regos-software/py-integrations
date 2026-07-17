from typing import Optional

from core.logger import setup_logger
from schemas.api.docs.order_delivery import (
    DocOrderDelivery,
    DocOrderDeliveryAddFullRequest,
    DocOrderDeliveryAddFullResponse,
    DocOrderDeliveryGetRequest,
    DocOrderDeliveryGetResponse,
    DocOrderDeliveryOperationGetRequest,
    DocOrderDeliveryOperationGetResponse,
    DocOrderDeliverySetStatusRequest,
    DocOrderDeliverySetStatusResponse,
)

logger = setup_logger("docs.OrderDelivery")


class DocOrderDeliveryService:
    PATH_GET = "DocOrderDelivery/Get"
    PATH_GET_POS = "POS/DocOrderDelivery/Get"
    PATH_ADD_FULL = "DocOrderDelivery/AddFull"
    PATH_SET_STATUS = "DocOrderDelivery/SetStatus"
    PATH_OPERATION_GET = "OrderDeliveryOperation/get"

    def __init__(self, api):
        self.api = api

    async def get(
        self,
        req: DocOrderDeliveryGetRequest,
        *,
        use_pos: bool = False,
    ) -> DocOrderDeliveryGetResponse:
        """Get retail order delivery documents."""
        path = self.PATH_GET_POS if use_pos else self.PATH_GET
        return await self.api.call(path, req, DocOrderDeliveryGetResponse)

    async def get_by_id(
        self,
        doc_id: int,
        *,
        use_pos: bool = False,
    ) -> Optional[DocOrderDelivery]:
        """Get one retail order delivery document by id."""
        resp = await self.get(DocOrderDeliveryGetRequest(ids=[doc_id]), use_pos=use_pos)
        return resp.result[0] if resp.result else None

    async def add_full(
        self, req: DocOrderDeliveryAddFullRequest
    ) -> DocOrderDeliveryAddFullResponse:
        """Create a retail order delivery document with operations."""
        return await self.api.call(
            self.PATH_ADD_FULL,
            req,
            DocOrderDeliveryAddFullResponse,
        )

    async def set_status(
        self, req: DocOrderDeliverySetStatusRequest
    ) -> DocOrderDeliverySetStatusResponse:
        """Set retail order delivery status."""
        return await self.api.call(
            self.PATH_SET_STATUS,
            req,
            DocOrderDeliverySetStatusResponse,
        )

    async def get_operations(
        self, req: DocOrderDeliveryOperationGetRequest
    ) -> DocOrderDeliveryOperationGetResponse:
        """Get retail order delivery operations."""
        return await self.api.call(
            self.PATH_OPERATION_GET,
            req,
            DocOrderDeliveryOperationGetResponse,
        )
