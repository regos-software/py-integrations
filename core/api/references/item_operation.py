from __future__ import annotations

from core.logger import setup_logger
from schemas.api.references.item_operation import (
    ItemOperationGetRequest,
    ItemOperationGetResponse,
)

logger = setup_logger("references.ItemOperation")


class ItemOperationService:
    PATH_GET = "ItemOperation/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ItemOperationGetRequest) -> ItemOperationGetResponse:
        return await self.api.call(self.PATH_GET, req, ItemOperationGetResponse)
