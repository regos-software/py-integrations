from typing import List, Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, ArrayResult, IDRequest
from schemas.api.docs.inventory import (
    DocInventory,
    DocInventoryAddRequest,
    DocInventoryAddResult,
    DocInventoryEditRequest,
    DocInventoryGetRequest,
)

logger = setup_logger("docs.Inventory")


class DocInventoryService:
    PATH_GET = "DocInventory/Get"
    PATH_ADD = "DocInventory/Add"
    PATH_EDIT = "DocInventory/Edit"
    PATH_CLOSE = "DocInventory/Close"
    PATH_OPEN = "DocInventory/Open"
    PATH_LOCK = "DocInventory/Lock"
    PATH_UNLOCK = "DocInventory/Unlock"
    PATH_DELETE_MARK = "DocInventory/DeleteMark"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: DocInventoryGetRequest
    ) -> APIBaseResponse[List[DocInventory]]:
        resp = await self.api.call(
            self.PATH_GET, req, APIBaseResponse[List[DocInventory]]
        )
        return resp

    async def get_by_id(self, id_: int) -> Optional[DocInventory]:
        resp = await self.get(DocInventoryGetRequest(ids=[id_]))
        return resp.result[0] if resp.result else None

    async def add(
        self, req: DocInventoryAddRequest
    ) -> APIBaseResponse[DocInventoryAddResult]:
        return await self.api.call(
            self.PATH_ADD, req, APIBaseResponse[DocInventoryAddResult]
        )

    async def edit(self, req: DocInventoryEditRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse[ArrayResult])

    async def close(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_CLOSE, req, APIBaseResponse[ArrayResult])

    async def open(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_OPEN, req, APIBaseResponse[ArrayResult])

    async def lock(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_LOCK, req, APIBaseResponse[ArrayResult])

    async def unlock(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_UNLOCK, req, APIBaseResponse[ArrayResult])

    async def delete_mark(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(
            self.PATH_DELETE_MARK, req, APIBaseResponse[ArrayResult]
        )
