from typing import List, Iterable, Optional, Sequence
from pydantic import TypeAdapter, ValidationError

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.item_group import ItemGroupGetRequest, ItemGroupGetResponse

logger = setup_logger("references.Item")


class ItemGroupService:
    PATH_GET = "ItemGroup/Get"

    def __init__(self, api):
        self.api = api

    async def get_raw(self, req: ItemGroupGetRequest) -> ItemGroupGetResponse:
        try:
            resp = await self.api.call(self.PATH_GET, req, ItemGroupGetResponse)
        except Exception:
            logger.exception("ItemGroup/Get failed")
            return ItemGroupGetResponse(ok=False)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            logger.warning(
                "ItemGroup/Get: unexpected result=%r", getattr(resp, "result", None)
            )
            return ItemGroupGetResponse(ok=False)
        return resp
