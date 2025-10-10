from typing import List, Iterable, Optional, Sequence
from pydantic import TypeAdapter, ValidationError

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.item import (
    Item,
    ItemGetExtResponse,
    ItemGetResponse,
    ItemSearchRequest,
    ItemGetRequest,
    ItemGetExtRequest,
    ItemExt,
)

logger = setup_logger("refrences.Item")


class ItemService:
    PATH_SEARCH = "Item/Search"
    PATH_GET = "Item/Get"
    PATH_GET_EXT = "Item/GetExt"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ItemGetRequest) -> ItemGetResponse:
        try:
            resp = await self.api.call(self.PATH_GET, req, ItemGetResponse)
        except Exception:
            logger.exception("Item/Get failed")
            return []
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning(
                "Item/Get: unexpected result=%r", getattr(resp, "result", None)
            )
            return ItemGetResponse(ok=False)
        return resp

    async def get_ext(self, req: ItemGetExtRequest) -> ItemGetExtResponse:
        try:
            resp = await self.api.call(self.PATH_GET_EXT, req, ItemGetExtResponse)
        except Exception:
            logger.exception("Item/GetExt failed")
            return ItemGetExtResponse(ok=False)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning(
                "Item/GetExt: unexpected result=%r", getattr(resp, "result", None)
            )
            return ItemGetExtResponse(ok=False)
        return resp

    async def search(self, req: ItemSearchRequest) -> APIBaseResponse:
        try:
            resp = await self.api.call(self.PATH_SEARCH, req, APIBaseResponse)
        except Exception:
            logger.exception("Item/Search failed")
            return []
        if not getattr(resp, "ok", False) or not isinstance(resp.result, dict):
            logger.warning(
                "Item/Search: unexpected result=%r", getattr(resp, "result", None)
            )
            return []
        return resp
