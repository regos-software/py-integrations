# services/stock.py
from __future__ import annotations

import functools
from typing_extensions import deprecated
import warnings
from typing import Iterable, List, Tuple

from pydantic import TypeAdapter

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.stock import (
    Stock,
    StockGetRequest,
    StockGetResponse,  # BC: используем для устаревшего метода _get
)

logger = setup_logger("refrences.Stock")


class StockService:
    PATH_GET = "Stock/Get"

    def __init__(self, api):
        self.api = api

    # ---------- RAW слой (1:1 к эндпоинтам, стандарт) ----------
    async def get_raw(self, req: StockGetRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    # ---------- Тонкие методы (стандарт) ----------
    async def get(self, req: StockGetRequest) -> List[Stock]:
        """
        Возвращает список складов.
        Бросает:
          - RuntimeError при ok=False
          - TypeError, если result не list
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Stock/Get ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False")
        if not isinstance(resp.result, list):
            logger.error("Stock/Get unexpected result format: %r", resp.result)
            raise TypeError("Stock/Get: ожидался list в result")
        return TypeAdapter(List[Stock]).validate_python(resp.result)

    async def get_page(self, req: StockGetRequest) -> Tuple[List[Stock], int, int]:
        """
        Возвращает (items, next_offset, total). Пагинация не скрывается.
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Stock/Get ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False")
        if not isinstance(resp.result, list):
            logger.error("Stock/Get unexpected result format: %r", resp.result)
            raise TypeError("Stock/Get: ожидался list в result")
        items = TypeAdapter(List[Stock]).validate_python(resp.result)
        next_offset = getattr(resp, "next_offset", None) or 0
        total = getattr(resp, "total", None) or len(items)
        return items, next_offset, total

    async def get_by_ids(self, ids: Iterable[int]) -> List[Stock]:
        """
        Удобство: получить склады по списку ID (если StockGetRequest поддерживает ids).
        """
        ids_list = list(ids)
        if not ids_list:
            return []
        return await self.get(StockGetRequest(ids=ids_list))  # type: ignore[arg-type]

    # ---------- Backward compatibility ----------
    # Сохраняем старый приватный метод _get, но помечаем как устаревший и
    # сохраняем прежний тип ответа (StockGetResponse).
    @deprecated("use get_raw() (APIBaseResponse) or get()/get_page() instead")
    async def _get(self, req: StockGetRequest) -> StockGetResponse:
        try:
            # Старое поведение: сразу просим типизированный ответ
            resp = await self.api.call(self.PATH_GET, req, StockGetResponse)
        except Exception:
            logger.exception("Stock/Get failed")
            return StockGetResponse(ok=False)

        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning("Stock/Get: unexpected result=%r", getattr(resp, "result", None))
            return StockGetResponse(ok=False)

        return resp
