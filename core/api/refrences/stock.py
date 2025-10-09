from typing import List, Iterable, Optional, Sequence
from pydantic import TypeAdapter, ValidationError

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.stock import Stock, StockGetRequest, StockGetResponse

logger = setup_logger("refrences.Stock")


class StockService:
    PATH_GET = "Stock/Get"

    def __init__(self, api):
        self.api = api

    async def _get(self, req: StockGetRequest) -> StockGetResponse:

        try:
            resp = await self.api.call(self.PATH_GET, req, StockGetResponse)
        except Exception:
            logger.exception("Stock/Get failed")
            return StockGetResponse(ok=False)

        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning(
                "Stock/Get: unexpected result=%r", getattr(resp, "result", None)
            )
            return StockGetResponse(ok=False)

        return resp

    async def get(self, req: StockGetRequest) -> List[Stock]:
        resp = await self._get(req)
        result = [Stock.model_validate(item) for item in resp.result or []]
        return result
