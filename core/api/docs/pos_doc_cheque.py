"""REGOS API service for PosDocCheque."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PosDocChequeService(RegosAPIService):
    PATH_GET = "pos/DocCheque/get"
    PATH_GETCURRENT = "pos/DocCheque/getcurrent"
    PATH_GET_CLOSED = "pos/DocCheque/GetClosed"
    PATH_CREATE = "pos/DocCheque/Create"
    PATH_SET_REFUND_INFO = "pos/DocCheque/SetRefundInfo"
    PATH_SET_QR_CODE_URL = "pos/DocCheque/SetQrCodeUrl"
    PATH_ADD_SELLER = "pos/DocCheque/AddSeller"
    PATH_REMOVE_SELLER = "pos/DocCheque/RemoveSeller"
    PATH_PAY = "pos/DocCheque/Pay"
    PATH_CLOSE = "pos/DocCheque/Close"
    PATH_DELAY = "pos/DocCheque/Delay"
    PATH_CONTINUE_DELAYED = "pos/DocCheque/ContinueDelayed"
    PATH_CANCEL = "pos/DocCheque/Cancel"
    PATH_BACK_TO_OPERATIONS = "pos/DocCheque/BackToOperations"
    PATH_SET_PERCENT_DISCOUNT = "pos/DocCheque/SetPercentDiscount"
    PATH_SET_AMOUNT_DISCOUNT = "pos/DocCheque/SetAmountDiscount"
    PATH_ADD_RETAIL_CARD = "pos/DocCheque/AddRetailCard"
    PATH_SET_RETURN = "pos/DocCheque/SetReturn"
    PATH_SET_DOC_ORDER_DELIVERY = "pos/DocCheque/SetDocOrderDelivery"
    PATH_GET_PRINTED = "pos/DocCheque/getPrinted"
    PATH_GET_TEST_PRINTED = "pos/DocCheque/getTestPrinted"
    PATH_PAY_DEBT = "pos/DocCheque/PayDebt"
    REQUEST_MODELS = {
        'add_retail_card': models.Cheque_AddRetailCard,
        'add_seller': models.SetSeller,
        'back_to_operations': models.ChequeUuid,
        'cancel': models.ChequeUuid,
        'close': models.ChequeUuid,
        'continue_delayed': models.ChequeUuid,
        'delay': models.ChequeUuid,
        'get': models.ChequeGet,
        'get_printed': models.ChequePrint_RequestModel,
        'get_test_printed': models.ChequeTestPrintRequestModel,
        'pay': models.ChequeUuid,
        'pay_debt': models.Cheque_AddPayDebt,
        'remove_seller': models.RemoveSeller,
        'set_amount_discount': models.Cheque_SetAmountDiscount,
        'set_doc_order_delivery': models.Cheque_SetDocOrderDelivery,
        'set_percent_discount': models.Cheque_SetPercentDiscount,
        'set_qr_code_url': models.SetQrCodeUrl,
        'set_refund_info': models.SetRefundInfo,
        'set_return': models.Cheque_SetIsReturn,
    }

    async def get(self, req: models.ChequeGet | dict[str, Any]) -> models.ChequeArrayRegosObjectResult:
        """POST pos/DocCheque/get."""
        return await self._call(self.PATH_GET, req, models.ChequeArrayRegosObjectResult)

    async def getcurrent(self, body: dict[str, Any] | None = None) -> models.ChequeArrayRegosObjectResult:
        """POST pos/DocCheque/getcurrent."""
        return await self._call(self.PATH_GETCURRENT, body or {}, models.ChequeArrayRegosObjectResult)

    async def get_closed(self, body: dict[str, Any] | None = None) -> models.ChequeArrayRegosObjectResult:
        """POST pos/DocCheque/GetClosed."""
        return await self._call(self.PATH_GET_CLOSED, body or {}, models.ChequeArrayRegosObjectResult)

    async def create(self, body: dict[str, Any] | None = None) -> models.Insert_uuid_Result:
        """POST pos/DocCheque/Create."""
        return await self._call(self.PATH_CREATE, body or {}, models.Insert_uuid_Result)

    async def set_refund_info(self, req: models.SetRefundInfo | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/SetRefundInfo."""
        return await self._call(self.PATH_SET_REFUND_INFO, req, models.UpdateResult)

    async def set_qr_code_url(self, req: models.SetQrCodeUrl | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/SetQrCodeUrl."""
        return await self._call(self.PATH_SET_QR_CODE_URL, req, models.UpdateResult)

    async def add_seller(self, req: models.SetSeller | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/AddSeller."""
        return await self._call(self.PATH_ADD_SELLER, req, models.UpdateResult)

    async def remove_seller(self, req: models.RemoveSeller | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/RemoveSeller."""
        return await self._call(self.PATH_REMOVE_SELLER, req, models.UpdateResult)

    async def pay(self, req: models.ChequeUuid | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/Pay."""
        return await self._call(self.PATH_PAY, req, models.UpdateResult)

    async def close(self, req: models.ChequeUuid | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/Close."""
        return await self._call(self.PATH_CLOSE, req, models.UpdateResult)

    async def delay(self, req: models.ChequeUuid | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/Delay."""
        return await self._call(self.PATH_DELAY, req, models.UpdateResult)

    async def continue_delayed(self, req: models.ChequeUuid | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/ContinueDelayed."""
        return await self._call(self.PATH_CONTINUE_DELAYED, req, models.UpdateResult)

    async def cancel(self, req: models.ChequeUuid | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/Cancel."""
        return await self._call(self.PATH_CANCEL, req, models.UpdateResult)

    async def back_to_operations(self, req: models.ChequeUuid | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/BackToOperations."""
        return await self._call(self.PATH_BACK_TO_OPERATIONS, req, models.UpdateResult)

    async def set_percent_discount(self, req: models.Cheque_SetPercentDiscount | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/SetPercentDiscount."""
        return await self._call(self.PATH_SET_PERCENT_DISCOUNT, req, models.UpdateResult)

    async def set_amount_discount(self, req: models.Cheque_SetAmountDiscount | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/SetAmountDiscount."""
        return await self._call(self.PATH_SET_AMOUNT_DISCOUNT, req, models.UpdateResult)

    async def add_retail_card(self, req: models.Cheque_AddRetailCard | dict[str, Any]) -> models.ChequeArrayRegosObjectResult:
        """POST pos/DocCheque/AddRetailCard."""
        return await self._call(self.PATH_ADD_RETAIL_CARD, req, models.ChequeArrayRegosObjectResult)

    async def set_return(self, req: models.Cheque_SetIsReturn | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/SetReturn."""
        return await self._call(self.PATH_SET_RETURN, req, models.UpdateResult)

    async def set_doc_order_delivery(self, req: models.Cheque_SetDocOrderDelivery | dict[str, Any]) -> models.UpdateResult:
        """POST pos/DocCheque/SetDocOrderDelivery."""
        return await self._call(self.PATH_SET_DOC_ORDER_DELIVERY, req, models.UpdateResult)

    async def get_printed(self, req: models.ChequePrint_RequestModel | dict[str, Any]) -> models.ChequePrint_ResponseModelRegosObjectResult:
        """POST pos/DocCheque/getPrinted."""
        return await self._call(self.PATH_GET_PRINTED, req, models.ChequePrint_ResponseModelRegosObjectResult)

    async def get_test_printed(self, req: models.ChequeTestPrintRequestModel | dict[str, Any]) -> models.ChequePrint_ResponseModelRegosObjectResult:
        """POST pos/DocCheque/getTestPrinted."""
        return await self._call(self.PATH_GET_TEST_PRINTED, req, models.ChequePrint_ResponseModelRegosObjectResult)

    async def pay_debt(self, req: models.Cheque_AddPayDebt | dict[str, Any]) -> models.ChequeRegosObjectResult:
        """POST pos/DocCheque/PayDebt."""
        return await self._call(self.PATH_PAY_DEBT, req, models.ChequeRegosObjectResult)

__all__ = ['PosDocChequeService']
