from typing import List, Iterable, Optional, Sequence
from pydantic import TypeAdapter, ValidationError

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.item import (
    Item, ItemSearchRequest, ItemGetRequest, ItemGetExtRequest, ItemExt
)

logger = setup_logger("refrences.Item")


class ItemService:
    PATH_SEARCH = "Item/Search"
    PATH_GET = "Item/Get"
    PATH_GET_EXT = "Item/GetExt"

    def __init__(self, api):
        self.api = api

    # --- Search -> list[int] ---
    async def search(self, req: ItemSearchRequest) -> List[int]:
        try:
            resp = await self.api.call(self.PATH_SEARCH, req, APIBaseResponse)
        except Exception:
            logger.exception("Item/Search failed")
            return []
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning("Item/Search: unexpected result=%r", getattr(resp, "result", None))
            return []
        try:
            ta = TypeAdapter(List[int])
            ids = ta.validate_python(resp.result)
        except ValidationError:
            # иногда backend может прислать строки-числа — попробуем мягко привести
            ids = []
            for v in resp.result:
                try:
                    ids.append(int(v))
                except Exception:
                    pass
        logger.debug("Item/Search -> %d ids", len(ids))
        # backend ограничивает до 100, но не помешает урезать сами
        return ids[:100]

    # --- Get -> list[Item] ---
    async def get(self, req: ItemGetRequest) -> List[Item]:
        try:
            resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        except Exception:
            logger.exception("Item/Get failed")
            return []
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning("Item/Get: unexpected result=%r", getattr(resp, "result", None))
            return []
        ta = TypeAdapter(List[Item])
        items = ta.validate_python(resp.result)
        logger.debug("Item/Get -> %d items", len(items))
        return items

    # --- Удобство: по ids (с чанками, чтобы не упираться в ограничения запроса) ---
    async def get_by_ids(self, ids: Iterable[int], chunk_size: int = 50) -> List[Item]:
        ids_list = list(ids)
        if not ids_list:
            return []
        out: List[Item] = []
        for i in range(0, len(ids_list), chunk_size):
            part = ids_list[i:i + chunk_size]
            out.extend(await self.get(ItemGetRequest(ids=part)))
        return out

    # --- GetExt -> list[ItemExt] ---
    async def get_ext(self, req: ItemGetExtRequest) -> List[ItemExt]:
        try:
            resp = await self.api.call(self.PATH_GET_EXT, req, APIBaseResponse)
        except Exception:
            logger.exception("Item/GetExt failed")
            return []
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning("Item/GetExt: unexpected result=%r", getattr(resp, "result", None))
            return []
        ta = TypeAdapter(List[ItemExt])
        items_ext = ta.validate_python(resp.result)
        logger.debug("Item/GetExt -> %d rows", len(items_ext))
        return items_ext

    # --- Удобство: поиск по строке и получение Item (Search -> ids -> Get) ---
    async def search_and_get(self, query: str) -> List[Item]:
        # пробуем по всем полям (backend требует минимум одно из code/name/articul/barcode)
        ids = await self.search(ItemSearchRequest(
            barcode=query, code=query, articul=query, name=query
        ))
        if not ids:
            return []
        return await self.get_by_ids(ids)

    # --- Альтернатива: сразу искать расширенные карточки по тексту (через GetExt) ---
    async def search_and_get_ext(self, query: str, *, stock_id: Optional[int] = None,
                             price_type_id: Optional[int] = None, limit: int = 50) -> List[ItemExt]:
        req = ItemGetExtRequest(
            search=query,
            stock_id=stock_id,
            price_type_id=price_type_id,
            limit=limit,
            offset=0
        )
        return await self.get_ext(req)
