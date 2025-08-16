from typing import Optional
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.docs.cash_operation import CashOperation, CashOperationGetRequest
from schemas.api.docs.cash_amount_details import CashAmountDetails, CashAmountDetailsGetRequest

logger = setup_logger("docs.CashOperation")


class CashOperationService:
    PATH_GET = "CashOperation/Get"
    PATH_GET_AMOUNT_DETAILS = "CashOperation/GetAmountDetails"

    def __init__(self, api):
        self.api = api

    async def get(self, req: CashOperationGetRequest) -> list[CashOperation]:
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [CashOperation.model_validate(x) for x in resp.result]

    async def get_amount_details(self, req: CashAmountDetailsGetRequest) -> Optional[CashAmountDetails]:
        """
        POST …/v1/CashOperation/GetAmountDetails
        Возвращает детали по денежным средствам в кассе.
        """
        resp = await self.api.call(self.PATH_GET_AMOUNT_DETAILS, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or resp.result is None:
            return None
        return CashAmountDetails.model_validate(resp.result)
