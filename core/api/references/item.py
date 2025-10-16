# services/item.py
from __future__ import annotations

from typing import List


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

    async def search(self, req: ItemSearchRequest) -> APIBaseResponse[List[int]]:
        return await self.api.call(self.PATH_SEARCH, req, APIBaseResponse[List[int]])

    async def get(self, req: ItemGetRequest) -> APIBaseResponse[Item]:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse[Item])

    async def get_ext(self, req: ItemGetExtRequest) -> APIBaseResponse[ItemExt]:
        return await self.api.call(self.PATH_GET_EXT, req, APIBaseResponse[ItemExt])
