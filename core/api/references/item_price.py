from __future__ import annotations

from core.logger import setup_logger
from schemas.api.references.item_price import (
    ItemPriceGetPreCostRequest,
    ItemPriceGetPreCostResponse,
    ItemPriceGetRequest,
    ItemPriceGetResponse,
)

logger = setup_logger("references.ItemPrice")


class ItemPriceService:
    PATH_GET = "ItemPrice/Get"
    PATH_GET_PRE_COST = "ItemPrice/GetPreCost"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ItemPriceGetRequest) -> ItemPriceGetResponse:
        return await self.api.call(self.PATH_GET, req, ItemPriceGetResponse)

    async def get_pre_cost(
        self, req: ItemPriceGetPreCostRequest
    ) -> ItemPriceGetPreCostResponse:
        return await self.api.call(
            self.PATH_GET_PRE_COST,
            req,
            ItemPriceGetPreCostResponse,
        )
