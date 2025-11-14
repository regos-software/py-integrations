from typing import Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, ArrayResult, IDRequest
from schemas.api.docs.movement import (
    DocMovement,
    DocMovementAddRequest,
    DocMovementGetRequest,
    DocMovementGetResponse,
)

logger = setup_logger("docs.Movement")


class DocMovementService:
    PATH_GET = "DocMovement/Get"
    PATH_PERFORM = "DocMovement/Perform"
    PATH_ADD = "DocMovement/Add"
    PATH_PERFORM_CANCEL = "DocMovement/PerformCancel"
    PATH_LOCK = "DocMovement/Lock"
    PATH_UNLOCK = "DocMovement/Unlock"
    PATH_DELETE_MARK = "DocMovement/DeleteMark"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DocMovementGetRequest) -> DocMovementGetResponse:
        """Получить список документов перемещения."""
        return await self.api.call(self.PATH_GET, req, DocMovementGetResponse)

    async def get_by_id(self, doc_id: int) -> Optional[DocMovement]:
        """Получить документ перемещения по идентификатору."""
        resp = await self.get(DocMovementGetRequest(ids=[doc_id]))
        return resp.result[0] if resp.result else None

    async def add(self, req: DocMovementAddRequest) -> APIBaseResponse:
        """Создать новый документ перемещения."""
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse)

    async def perform(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """Провести документ перемещения."""
        return await self.api.call(self.PATH_PERFORM, req, APIBaseResponse[ArrayResult])

    async def perform_cancel(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """Отменить проведение документа перемещения."""
        return await self.api.call(
            self.PATH_PERFORM_CANCEL, req, APIBaseResponse[ArrayResult]
        )

    async def lock(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """Заблокировать документ перемещения."""
        return await self.api.call(self.PATH_LOCK, req, APIBaseResponse[ArrayResult])

    async def unlock(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """Разблокировать документ перемещения."""
        return await self.api.call(self.PATH_UNLOCK, req, APIBaseResponse[ArrayResult])

    async def delete_mark(self, req: IDRequest) -> APIBaseResponse[ArrayResult]:
        """Пометить документ перемещения на удаление."""
        return await self.api.call(
            self.PATH_DELETE_MARK, req, APIBaseResponse[ArrayResult]
        )
