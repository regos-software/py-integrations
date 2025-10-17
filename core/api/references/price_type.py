from __future__ import annotations

from core.logger import setup_logger
from schemas.api.references.price_type import (
    PriceTypeGetRequest,
    PriceTypeGetResponse,
)

logger = setup_logger("references.PriceType")


class PriceTypeService:
    PATH_GET = "PriceType/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: PriceTypeGetRequest) -> PriceTypeGetResponse:
        return await self.api.call(self.PATH_GET, req, PriceTypeGetResponse)
