from __future__ import annotations
from decimal import Decimal
from typing import Type, TypeVar, Any
from fastapi.encoders import jsonable_encoder
import httpx
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)

from core.api.batch import BatchService
from core.api.client import APIClient
from core.api.references.item_group import ItemGroupService
from core.api.references.stock import StockService
from core.logger import setup_logger

logger = setup_logger("regos_api")
T = TypeVar("T")


class RegosAPI:
    def __init__(self, connected_integration_id: str):
        self.connected_integration_id = connected_integration_id
        self._client = APIClient(connected_integration_id=connected_integration_id)
        self.batch = BatchService(self._client)

        self.docs: "RegosAPI.Docs" = self.Docs(self)
        self.integrations: "RegosAPI.Integrations" = self.Integrations(self)
        self.reports: "RegosAPI.Reports" = self.Reports(self)
        self.references: "RegosAPI.references" = self.references(self)

    @retry(
        wait=wait_exponential(min=0.2, max=5),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def call(self, path: str, body: Any, response_model: Type[T]) -> T:
        return await self._client.post(
            method_path=path, data=body, response_model=response_model
        )

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "RegosAPI":
        return self

    async def __aexit__(self, *_):
        await self.close()

    # ------- Namespaces -------
    class Docs:
        def __init__(self, api: "RegosAPI"):
            from core.api.docs.cheque import DocsChequeService
            from core.api.docs.cash_session import DocCashSessionService
            from core.api.docs.cheque_operation import DocChequeOperationService
            from core.api.docs.retail_payment import DocRetailPaymentService
            from core.api.docs.cash_operation import CashOperationService
            from core.api.docs.purchase import DocPurchaseService
            from core.api.docs.purchase_operation import PurchaseOperationService
            from core.api.docs.wholesale import DocWholeSaleService
            from core.api.docs.wholesale_operation import WholeSaleOperationService

            # Initialize services

            self.cheque = DocsChequeService(api)
            self.cash_session = DocCashSessionService(api)
            self.cheque_operation = DocChequeOperationService(api)
            self.retail_payment = DocRetailPaymentService(api)
            self.cash_operation = CashOperationService(api)
            self.purchase = DocPurchaseService(api)
            self.purchase_operation = PurchaseOperationService(api)
            self.wholesale = DocWholeSaleService(api)
            self.wholesale_operation = WholeSaleOperationService(api)

    class Integrations:
        def __init__(self, api: "RegosAPI"):
            from core.api.integrations.connected_integration_setting import (
                ConnectedIntegrationSettingService,
            )

            self.connected_integration_setting = ConnectedIntegrationSettingService(api)

    class Reports:
        def __init__(self, api: "RegosAPI"):
            from core.api.reports.retail_report import RetailReportService

            self.retail_report = RetailReportService(api)

    class references:
        def __init__(self, api: "RegosAPI"):

            from core.api.references.item import ItemService

            self.item = ItemService(api)
            self.item_group = ItemGroupService(api)
            self.stock = StockService(api)
