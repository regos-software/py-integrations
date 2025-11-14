from typing import List

from schemas.api.base import APIBaseResponse
from schemas.api.docs.movement_operation import (
    MovementOperation,
    MovementOperationActionResponse,
    MovementOperationAddRequest,
    MovementOperationDeleteItem,
    MovementOperationEditItem,
    MovementOperationGetRequest,
)


class MovementOperationService:
    PATH_GET = "MovementOperation/Get"
    PATH_ADD = "MovementOperation/Add"
    PATH_EDIT = "MovementOperation/Edit"
    PATH_DELETE = "MovementOperation/Delete"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: MovementOperationGetRequest
    ) -> APIBaseResponse[List[MovementOperation]]:
        return await self.api.call(
            self.PATH_GET, req, APIBaseResponse[List[MovementOperation]]
        )

    async def get_by_document_id(self, doc_id: int) -> List[MovementOperation]:
        response = await self.get(MovementOperationGetRequest(document_ids=[doc_id]))
        return response.result or []

    async def add(
        self, req: List[MovementOperationAddRequest]
    ) -> MovementOperationActionResponse:
        return await self.api.call(self.PATH_ADD, req, MovementOperationActionResponse)

    async def edit(
        self, req: List[MovementOperationEditItem]
    ) -> MovementOperationActionResponse:
        return await self.api.call(self.PATH_EDIT, req, MovementOperationActionResponse)

    async def delete(
        self, req: List[MovementOperationDeleteItem]
    ) -> MovementOperationActionResponse:
        return await self.api.call(
            self.PATH_DELETE, req, MovementOperationActionResponse
        )
