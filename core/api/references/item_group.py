from typing import List
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.item_group import ItemGroup, ItemGroupGetRequest

logger = setup_logger("references.Item")


class ItemGroupService:
    PATH_GET = "ItemGroup/Get"

    def __init__(self, api: RegosAPI):
        self.api = api

    async def get(self, req: ItemGroupGetRequest) -> APIBaseResponse[List[ItemGroup]]:
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse[List[ItemGroup]])
        return resp
