# services/item.py
from __future__ import annotations

from typing import List


from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.item import (
    Item,
    ItemGetCurrentQuantityRequest,
    ItemGetCurrentQuantityResponse,
    ItemExt,
    ItemGetExtRequest,
    ItemGetQuantityRequest,
    ItemGetQuantityResponse,
    ItemGetRequest,
    ItemGetShortResponse,
    ItemImportRequest,
    ItemImportResponse,
    ItemMatchingRequest,
    ItemMatchingResponse,
    ItemSearchRequest,
)

logger = setup_logger("references.Item")


class ItemService:
    PATH_SEARCH = "Item/Search"
    PATH_GET = "Item/Get"
    PATH_GET_EXT = "Item/GetExt"
    PATH_GET_QUANTITY = "Item/GetQuantity"
    PATH_GET_CURRENT_QUANTITY = "Item/GetCurrentQuantity"
    PATH_GET_SHORT = "Item/GetShort"
    PATH_IMPORT = "Item/Import"
    PATH_MATCH = "Item/Match"

    def __init__(self, api):
        self.api = api

    async def search(self, req: ItemSearchRequest) -> APIBaseResponse[List[int]]:
        return await self.api.call(self.PATH_SEARCH, req, APIBaseResponse[List[int]])

    async def get(self, req: ItemGetRequest) -> APIBaseResponse[List[Item]]:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse[List[Item]])

    async def get_ext(self, req: ItemGetExtRequest) -> APIBaseResponse[List[ItemExt]]:
        return await self.api.call(
            self.PATH_GET_EXT, req, APIBaseResponse[List[ItemExt]]
        )

    async def get_quantity(
        self, req: ItemGetQuantityRequest
    ) -> ItemGetQuantityResponse:
        return await self.api.call(
            self.PATH_GET_QUANTITY,
            req,
            ItemGetQuantityResponse,
        )

    async def get_current_quantity(
        self, req: ItemGetCurrentQuantityRequest
    ) -> ItemGetCurrentQuantityResponse:
        return await self.api.call(
            self.PATH_GET_CURRENT_QUANTITY,
            req,
            ItemGetCurrentQuantityResponse,
        )

    async def get_short(self, req: ItemGetRequest) -> ItemGetShortResponse:
        return await self.api.call(self.PATH_GET_SHORT, req, ItemGetShortResponse)

    async def import_items(self, req: ItemImportRequest) -> ItemImportResponse:
        return await self.api.call(self.PATH_IMPORT, req, ItemImportResponse)

    async def match(self, req: ItemMatchingRequest) -> ItemMatchingResponse:
        return await self.api.call(self.PATH_MATCH, req, ItemMatchingResponse)
