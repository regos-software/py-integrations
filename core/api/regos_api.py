from __future__ import annotations
import asyncio
from typing import Any, Dict, Optional, Type, TypeVar

import httpx
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)

from core.api.batch import BatchService
from core.api.client import APIClient

from core.logger import setup_logger

logger = setup_logger("regos_api")
T = TypeVar("T")


class RegosAPI:
    _shared_clients: Dict[str, APIClient] = {}
    _shared_ref_counts: Dict[str, int] = {}
    _shared_close_tasks: Dict[str, asyncio.Task] = {}
    _shared_lock: Optional[asyncio.Lock] = None
    _shared_idle_close_sec = 30

    def __init__(self, connected_integration_id: str):
        self.connected_integration_id = connected_integration_id
        self._shared_key = str(connected_integration_id or "").strip()
        self._client: Optional[APIClient] = None
        self._closed = False
        self.batch = BatchService(self)

        self.docs: "RegosAPI.Docs" = self.Docs(self)
        self.crm: "RegosAPI.Crm" = self.Crm(self)
        self.chat: "RegosAPI.Chat" = self.Chat(self)
        self.files: "RegosAPI.Files" = self.Files(self)
        self.integrations: "RegosAPI.Integrations" = self.Integrations(self)
        self.reports: "RegosAPI.Reports" = self.Reports(self)
        self.references: "RegosAPI.References" = self.References(self)
        self.rbac: "RegosAPI.Rbac" = self.Rbac(self)

    async def _acquire_client(self) -> APIClient:
        if self._client is not None:
            return self._client

        async with self._get_shared_lock():
            close_task = self._shared_close_tasks.pop(self._shared_key, None)
            if close_task and not close_task.done():
                close_task.cancel()

            client = self._shared_clients.get(self._shared_key)
            if client is None:
                client = APIClient(connected_integration_id=self.connected_integration_id)
                self._shared_clients[self._shared_key] = client
                self._shared_ref_counts[self._shared_key] = 0

            self._shared_ref_counts[self._shared_key] = (
                self._shared_ref_counts.get(self._shared_key, 0) + 1
            )

        self._client = client
        self._closed = False
        return client

    @classmethod
    def _get_shared_lock(cls) -> asyncio.Lock:
        if cls._shared_lock is None:
            cls._shared_lock = asyncio.Lock()
        return cls._shared_lock

    @classmethod
    async def _close_shared_client_later(cls, shared_key: str) -> None:
        try:
            await asyncio.sleep(max(int(cls._shared_idle_close_sec), 1))
        except asyncio.CancelledError:
            return

        client_to_close: Optional[APIClient] = None
        async with cls._get_shared_lock():
            if cls._shared_ref_counts.get(shared_key, 0) > 0:
                return
            client_to_close = cls._shared_clients.pop(shared_key, None)
            cls._shared_ref_counts.pop(shared_key, None)
            cls._shared_close_tasks.pop(shared_key, None)

        if client_to_close is None:
            return
        try:
            await client_to_close.close()
        except Exception:
            logger.exception("Failed to close shared API client: integration_id=%s", shared_key)

    @retry(
        wait=wait_exponential(min=0.2, max=5),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def call(self, path: str, body: Any, response_model: Type[T]) -> T:
        client = await self._acquire_client()
        return await client.post(
            method_path=path, data=body, response_model=response_model
        )

    @retry(
        wait=wait_exponential(min=0.2, max=5),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def call_multipart(
        self,
        path: str,
        data: dict[str, Any],
        files: dict[str, tuple[str, bytes] | tuple[str, bytes, str]],
        response_model: Type[T],
    ) -> T:
        client = await self._acquire_client()
        return await client.post_multipart(
            method_path=path,
            data=data,
            files=files,
            response_model=response_model,
        )

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._client is None:
            return

        async with self._get_shared_lock():
            current_refs = self._shared_ref_counts.get(self._shared_key, 0)
            next_refs = max(current_refs - 1, 0)
            self._shared_ref_counts[self._shared_key] = next_refs
            if next_refs == 0:
                close_task = self._shared_close_tasks.get(self._shared_key)
                if close_task and not close_task.done():
                    close_task.cancel()
                self._shared_close_tasks[self._shared_key] = asyncio.create_task(
                    self._close_shared_client_later(self._shared_key)
                )

        self._client = None

    async def __aenter__(self) -> "RegosAPI":
        await self._acquire_client()
        return self

    async def __aexit__(self, *_):
        await self.close()

    # ------- Namespaces -------
    class Docs:
        def __init__(self, api: "RegosAPI"):
            from core.api.docs.cheque import DocsChequeService
            from core.api.docs.cash_session import DocCashSessionService
            from core.api.docs.cheque_operation import DocChequeOperationService
            from core.api.docs.cheque_payment import DocChequePaymentService
            from core.api.docs.cash_operation import CashOperationService
            from core.api.docs.purchase import DocPurchaseService
            from core.api.docs.purchase_operation import PurchaseOperationService
            from core.api.docs.wholesale import DocWholeSaleService
            from core.api.docs.wholesale_operation import WholeSaleOperationService
            from core.api.docs.inventory import DocInventoryService
            from core.api.docs.inventory_operation import InventoryOperationService
            from core.api.docs.movement import DocMovementService
            from core.api.docs.movement_operation import MovementOperationService
            from core.api.docs.order_delivery import DocOrderDeliveryService

            # Initialize services

            self.cheque = DocsChequeService(api)
            self.cash_session = DocCashSessionService(api)
            self.cheque_operation = DocChequeOperationService(api)
            self.cheque_payment = DocChequePaymentService(api)
            self.cash_operation = CashOperationService(api)
            self.purchase = DocPurchaseService(api)
            self.purchase_operation = PurchaseOperationService(api)
            self.wholesale = DocWholeSaleService(api)
            self.wholesale_operation = WholeSaleOperationService(api)
            self.inventory = DocInventoryService(api)
            self.inventory_operation = InventoryOperationService(api)
            self.movement = DocMovementService(api)
            self.movement_operation = MovementOperationService(api)
            self.order_delivery = DocOrderDeliveryService(api)

    class Integrations:
        def __init__(self, api: "RegosAPI"):
            from core.api.integrations.connected_integration_setting import (
                ConnectedIntegrationSettingService,
            )

            self.connected_integration_setting = ConnectedIntegrationSettingService(api)

    class Crm:
        def __init__(self, api: "RegosAPI"):
            from core.api.crm.lead import LeadService
            from core.api.crm.pipeline import PipelineService

            self.lead = LeadService(api)
            self.pipeline = PipelineService(api)

    class Chat:
        def __init__(self, api: "RegosAPI"):
            from core.api.chat.chat_message import ChatMessageService

            self.chat_message = ChatMessageService(api)

    class Files:
        def __init__(self, api: "RegosAPI"):
            from core.api.files.file import FileService

            self.file = FileService(api)

    class Reports:
        def __init__(self, api: "RegosAPI"):
            from core.api.reports.retail_report import RetailReportService

            self.retail_report = RetailReportService(api)

    class References:
        def __init__(self, api: "RegosAPI"):

            from core.api.references.brand import BrandService
            from core.api.references.currency import CurrencyService
            from core.api.references.item import ItemService
            from core.api.references.item_group import ItemGroupService
            from core.api.references.partner import PartnerService
            from core.api.references.retail_customer import RetailCustomerService
            from core.api.references.stock import StockService
            from core.api.references.item_price import ItemPriceService
            from core.api.references.item_operation import ItemOperationService
            from core.api.references.price_type import PriceTypeService
            from core.api.references.operating_cash import OperatingCashService 
            from core.api.references.retail_card import RetailCardService

            self.brand = BrandService(api)
            self.currency = CurrencyService(api)
            self.retail_customer = RetailCustomerService(api)
            self.item = ItemService(api)
            self.item_group = ItemGroupService(api)
            self.stock = StockService(api)
            self.item_price = ItemPriceService(api)
            self.item_operation = ItemOperationService(api)
            self.price_type = PriceTypeService(api)
            self.partner = PartnerService(api)
            self.operating_cash = OperatingCashService(api)
            self.retail_card = RetailCardService(api)

    class Rbac:
        def __init__(self, api: "RegosAPI"):
            from core.api.rbac.user import UserService

            self.user = UserService(api)

    class Batch:
        def __init__(self, api: "RegosAPI"):
            self._service = BatchService(api)

        async def run(self, req):
            return await self._service.run(req)

        # add helpers (map/result/etc.) here if you want them reachable via router
