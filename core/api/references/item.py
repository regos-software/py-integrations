# services/item.py
from __future__ import annotations

from typing import List, Tuple

from pydantic import TypeAdapter, ValidationError

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.item import (
    Item,
    ItemExt,
    ItemGetExtRequest,
    ItemGetRequest,
    ItemSearchRequest,
)

logger = setup_logger("references.Item")


class ItemService:
    PATH_SEARCH = "Item/Search"
    PATH_GET = "Item/Get"
    PATH_GET_EXT = "Item/GetExt"

    def __init__(self, api):
        self.api = api

    # ---------- RAW слой (1:1 к эндпоинтам) ----------
    async def search_raw(self, req: ItemSearchRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_SEARCH, req, APIBaseResponse)

    async def get_raw(self, req: ItemGetRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    async def get_ext_raw(self, req: ItemGetExtRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET_EXT, req, APIBaseResponse)

    # ---------- Тонкие методы (рекомендуемый «стандарт») ----------
    async def search_ids(self, req: ItemSearchRequest) -> List[int]:
        """
        Строгий вариант поиска: возвращает список ID или бросает исключение.
        - ok=False -> RuntimeError
        - result не list -> TypeError
        - элементы приводим к int (мягкая попытка BC)
        """
        resp = await self.search_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/Search ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_SEARCH}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/Search unexpected result format: %r", resp.result)
            raise TypeError("Item/Search: ожидался list в result")

        # в идеале это строгая проверка...
        try:
            return TypeAdapter(List[int]).validate_python(resp.result)
        except ValidationError:
            # ...но для обратной совместимости попробуем мягко привести элементы к int
            out: List[int] = []
            for v in resp.result:
                try:
                    out.append(int(v))
                except Exception:
                    pass
            if not out and resp.result:
                # если совсем не удалось — считаем это ошибкой формата
                raise TypeError("Item/Search: элементы result не приводятся к int")
            return out

    async def get_items(self, req: ItemGetRequest) -> List[Item]:
        """
        Строгий вариант получения списка Item: возвращает список или бросает исключение.
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/Get ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/Get unexpected result format: %r", resp.result)
            raise TypeError("Item/Get: ожидался list в result")

        return TypeAdapter(List[Item]).validate_python(resp.result)

    async def get_page(self, req: ItemGetRequest) -> Tuple[List[Item], int, int]:
        """
        Возвращает (items, next_offset, total).
        Бросает исключение при ok=False/невалидном формате.
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/Get ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/Get unexpected result format: %r", resp.result)
            raise TypeError("Item/Get: ожидался list в result")

        items = TypeAdapter(List[Item]).validate_python(resp.result)
        next_offset = getattr(resp, "next_offset", None) or 0
        total = getattr(resp, "total", None) or len(items)
        return items, next_offset, total

    async def get_ext_items(self, req: ItemGetExtRequest) -> List[ItemExt]:
        """
        Строгий вариант расширенной выдачи.
        """
        resp = await self.get_ext_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/GetExt ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET_EXT}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/GetExt unexpected result format: %r", resp.result)
            raise TypeError("Item/GetExt: ожидался list в result")

        return TypeAdapter(List[ItemExt]).validate_python(resp.result)

    async def get_ext_page(
        self, req: ItemGetExtRequest
    ) -> Tuple[List[ItemExt], int, int]:
        """
        Возвращает (items_ext, next_offset, total) для расширенной выдачи.
        """
        resp = await self.get_ext_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/GetExt ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET_EXT}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/GetExt unexpected result format: %r", resp.result)
            raise TypeError("Item/GetExt: ожидался list в result")

        items_ext = TypeAdapter(List[ItemExt]).validate_python(resp.result)
        next_offset = getattr(resp, "next_offset", None) or 0
        total = getattr(resp, "total", None) or len(items_ext)
        return items_ext, next_offset, total
