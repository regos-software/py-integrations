# services/retail_customer.py
from __future__ import annotations

from typing import List, Tuple
from pydantic import TypeAdapter

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from core.api.docs.cheque import DocsChequeService
from core.api.docs.cheque_operation import DocChequeOperationService
from schemas.api.docs.cheque import DocChequeGetRequest, SortOrder as SortOrderCheque
from schemas.api.refrences.retail_customer import (
    RetailCustomer,
    RetailCustomerGetLastChequeRequest,
    RetailCustomerGetLastChequeResponse,
    RetailCustomerGetRequest,
    RetailCustomerAddRequest,
    RetailCustomerEditRequest,
    RetailCustomerDeleteMarkRequest,
    RetailCustomerDeleteRequest,
    RetailCustomerGetResponse,
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

    async def get(self, req: RetailCustomerGetRequest) -> APIBaseResponse:
        """
        Возвращает список покупателей. Бросает RuntimeError при ok=False
        и TypeError при неверном формате result.
        """
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    async def add(self, req: RetailCustomerAddRequest) -> APIBaseResponse:
        """
        Создаёт покупателя. Возвращает ID.
        """
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse)

    async def edit(self, req: RetailCustomerEditRequest) -> None:
        """
        Редактирует покупателя.
        """
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse)

    async def delete_mark(self, req: RetailCustomerDeleteMarkRequest) -> None:
        """
        Помечает покупателя на удаление.
        """
        return await self.api.call(self.PATH_DELETE_MARK, req, APIBaseResponse)

    async def delete(self, req: RetailCustomerDeleteRequest) -> None:
        """
        Полное удаление (возможно только при deleted_mark=true).
        """
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse)

    async def get_last_cheque(
        self, req: RetailCustomerGetLastChequeRequest
    ) -> RetailCustomerGetLastChequeResponse:
        """
        Приминимает ID покупателя и параметр detail
        Возвращает последний чек покупателя. (если не прошло месяц, т.к апи ищет чеки только за последний месяц)
        если detail=true, возвращает также массив операций чека (DocChequeOperations[]).
        """
        get_req = RetailCustomerGetRequest(ids=[req.id], limit=1)
        customer_response = await self.get(get_req)
        customer: RetailCustomer = (
            customer_response.result[0]
            if customer_response.result and len(customer_response.result) > 0
            else None
        )
        if not customer:
            return RetailCustomerGetLastChequeResponse(
                cheque=None, cheque_operations=None
            )

        cheque_response = await DocsChequeService(self.api).get(
            DocChequeGetRequest(
                customer_ids=[customer.id],
                limit=1,
                sort_orders=[SortOrderCheque(column="date", direction="DESC")],
            )
        )

        if not cheque_response:
            return RetailCustomerGetLastChequeResponse(
                cheque=None, cheque_operations=None
            )

        cheque = cheque_response[0]
        cheque_operations = None

        if req.detail:
            cheque_operations = await DocChequeOperationService(
                self.api
            ).get_by_doc_sale_uuid(cheque.uuid)

        return RetailCustomerGetLastChequeResponse(
            cheque=cheque,
            cheque_operations=cheque_operations,
        )
