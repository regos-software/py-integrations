# services/retail_customer.py
from __future__ import annotations
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, ArrayResult
from schemas.api.references.retail_customer import (
    RetailCustomerGetResponse,
    RetailCustomerGetRequest,
    RetailCustomerAddRequest,
    RetailCustomerEditRequest,
    RetailCustomerDeleteMarkRequest,
    RetailCustomerDeleteRequest,
)

logger = setup_logger("references.RetailCustomer")


class RetailCustomerService:
    PATH_GET = "RetailCustomer/Get"
    PATH_ADD = "RetailCustomer/Add"
    PATH_EDIT = "RetailCustomer/Edit"
    PATH_DELETE_MARK = "RetailCustomer/DeleteMark"
    PATH_DELETE = "RetailCustomer/Delete"

    def __init__(self, api):
        self.api = api

    async def get(self, req: RetailCustomerGetRequest) -> RetailCustomerGetResponse:
        """
        Возвращает список покупателей. Бросает RuntimeError при ok=False
        и TypeError при неверном формате result.
        """
        return await self.api.call(self.PATH_GET, req, RetailCustomerGetResponse)

    async def add(self, req: RetailCustomerAddRequest) -> APIBaseResponse[ArrayResult]:
        """
        Создаёт покупателя. Возвращает ID.
        """
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse[ArrayResult])

    async def edit(self, req: RetailCustomerEditRequest) -> None:
        """
        Редактирует покупателя.
        """
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse[ArrayResult])

    async def delete_mark(self, req: RetailCustomerDeleteMarkRequest) -> None:
        """
        Помечает покупателя на удаление.
        """
        return await self.api.call(
            self.PATH_DELETE_MARK, req, APIBaseResponse[ArrayResult]
        )

    async def delete(self, req: RetailCustomerDeleteRequest) -> None:
        """
        Полное удаление (возможно только при deleted_mark=true).
        """
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse[ArrayResult])
