# services/stock.py
from __future__ import annotations

from typing import List


from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.stock import (
    Stock,
    StockGetRequest,  # BC: используем для устаревшего метода _get
)

logger = setup_logger("references.Stock")


class StockService:
    PATH_GET = "Stock/Get"

    def __init__(self, api):
        self.api = api

    # ---------- RAW слой (1:1 к эндпоинтам, стандарт) ----------
    async def get(self, req: StockGetRequest) -> APIBaseResponse[List[Stock]]:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse[List[Stock]])
