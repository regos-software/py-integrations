from typing import List
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.reports.retail_report.count import Counts, CountsGetRequest
from schemas.api.reports.retail_report.payment import Payment, PaymentGetRequest


logger = setup_logger("reports.retail_report")


class RetailReportService:

    PATH_COUNTS = "RetailReport/Counts"
    PATH_PAYMENTS = "RetailReport/Payments"

    def __init__(self, api):
        self.api = api

    async def get_counts(self, req: CountsGetRequest) -> List[Counts]:
        """
        POST …/v1/RetailReport/Counts
        Возвращает список агрегатов Counts (по всему периоду и выбранным кассам).
        """
        resp = await self.api.call(self.PATH_COUNTS, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [Counts.model_validate(x) for x in resp.result]

    async def get_payments(self, req: PaymentGetRequest) -> List[Payment]:
        """
        POST …/v1/RetailReport/Payments
        Возвращает список Payments — суммы продаж/возвратов по формам оплаты.
        """
        resp = await self.api.call(self.PATH_PAYMENTS, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [Payment.model_validate(x) for x in resp.result]
