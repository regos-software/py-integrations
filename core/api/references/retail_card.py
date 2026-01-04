from typing import List

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.retail_card import (
    RetailCard,
    RetailCardGetRequest,
)

logger = setup_logger("references.RetailCard")


class RetailCardService:
    PATH_GET = "RetailCard/Get"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: RetailCardGetRequest
    ) -> APIBaseResponse[List[RetailCard]]:
        """Получить карты покупателей."""
        return await self.api.call(self.PATH_GET, req, APIBaseResponse[List[RetailCard]])
