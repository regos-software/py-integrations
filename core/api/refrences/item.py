from typing import List, Iterable, Tuple
from pydantic import TypeAdapter

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
        resp = await self.api.call(self.PATH_SEARCH, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        ta = TypeAdapter(List[int])
        return ta.validate_python(resp.result)

    # --- Get -> list[Item] (игнорируем next_offset/total, как в других сервисах) ---
    async def get(self, req: ItemGetRequest) -> List[Item]:
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        ta = TypeAdapter(List[Item])
        return ta.validate_python(resp.result)

    # Удобство: по ids
    async def get_by_ids(self, ids: Iterable[int]) -> List[Item]:
        return await self.get(ItemGetRequest(ids=list(ids)))

    # --- GetExt -> list[ItemExt] ---
    async def get_ext(self, req: ItemGetExtRequest) -> List[ItemExt]:
        resp = await self.api.call(self.PATH_GET_EXT, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        ta = TypeAdapter(List[ItemExt])
        return ta.validate_python(resp.result)

    # --- Удобство: поиск по строке и получение Item (Search -> ids -> Get) ---
    async def search_and_get(self, query: str) -> List[Item]:
        # пробуем по всем полям поиска
        ids = await self.search(ItemSearchRequest(
            barcode=query, code=query, articul=query, name=query
        ))
        if not ids:
            return []
        # урежем до 100 (ограничение на бэке)
        ids = ids[:100]
        return await self.get_by_ids(ids)
