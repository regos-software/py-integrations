from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.cash_operation import CashOperation, CashOperationGetRequest
from schemas.api.docs.cash_amount_details import (
    CashAmountDetails,
    CashAmountDetailsGetRequest,
)

logger = setup_logger("docs.CashOperation")


class CashOperationService:
    PATH_GET = "CashOperation/Get"
    PATH_GET_AMOUNT_DETAILS = "CashOperation/GetAmountDetails"

    def __init__(self, api):
        self.api: RegosAPI = api

    async def get(
        self, req: CashOperationGetRequest
    ) -> APIBaseResponse[list[CashOperation]]:
        resp = await self.api.call(
            self.PATH_GET, req, APIBaseResponse[list[CashOperation]]
        )
        return resp

    async def get_amount_details(
        self, req: CashAmountDetailsGetRequest
    ) -> APIBaseResponse[CashAmountDetails]:
        """
        POST …/v1/CashOperation/GetAmountDetails
        Возвращает детали по денежным средствам в кассе.
        """
        resp = await self.api.call(self.PATH_GET_AMOUNT_DETAILS, req, APIBaseResponse)
        return resp
