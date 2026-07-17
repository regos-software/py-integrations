"""REGOS API service for ChequeOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ChequeOperationService(RegosAPIService):
    PATH_DOC_GET = "ChequeItemOperation/Get"
    PATH_GET = "pos/ChequeItemOperation/get"
    PATH_ADD = "pos/ChequeItemOperation/add"
    PATH_ADD_BY_BARCODE = "pos/ChequeItemOperation/AddByBarcode"
    PATH_EDIT = "pos/ChequeItemOperation/Edit"
    PATH_STORNO = "pos/ChequeItemOperation/Storno"
    PATH_SET_PERCENT_DISCOUNT = "pos/ChequeItemOperation/SetPercentDiscount"
    REQUEST_MODELS = {
        'add': models.ChequePositionAdd,
        'add_by_barcode': models.ChequePosition_AddByBarcode,
        'edit': models.ChequePostion_Edit,
        'get': models.ChequePositionGet,
        'set_percent_discount': models.Cheque_SetRowPercentDiscount,
        'storno': models.ChequePosition_Storno,
    }

    @staticmethod
    def _is_doc_cheque_operation_request(req: Any) -> bool:
        if isinstance(req, models.DocChequeOperationGet):
            return True
        return isinstance(req, dict) and "doc_sale_uuid" in req

    async def get(
        self,
        req: models.ChequePositionGet | models.DocChequeOperationGet | dict[str, Any],
    ) -> (
        models.ChequePositionArrayRegosObjectResult
        | models.DocChequeOperationRegosArrayResult
    ):
        """POST pos/ChequeItemOperation/get."""
        if self._is_doc_cheque_operation_request(req):
            return await self._call(
                self.PATH_DOC_GET,
                req,
                models.DocChequeOperationRegosArrayResult,
            )
        return await self._call(self.PATH_GET, req, models.ChequePositionArrayRegosObjectResult)

    async def add(self, req: models.ChequePositionAdd | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST pos/ChequeItemOperation/add."""
        return await self._call(self.PATH_ADD, req, models.Insert_uuid_Result)

    async def add_by_barcode(self, req: models.ChequePosition_AddByBarcode | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST pos/ChequeItemOperation/AddByBarcode."""
        return await self._call(self.PATH_ADD_BY_BARCODE, req, models.Insert_uuid_Result)

    async def edit(self, req: models.ChequePostion_Edit | dict[str, Any]) -> models.UpdateResult:
        """POST pos/ChequeItemOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def storno(self, req: models.ChequePosition_Storno | dict[str, Any]) -> models.UpdateResult:
        """POST pos/ChequeItemOperation/Storno."""
        return await self._call(self.PATH_STORNO, req, models.UpdateResult)

    async def set_percent_discount(self, req: models.Cheque_SetRowPercentDiscount | dict[str, Any]) -> models.UpdateResult:
        """POST pos/ChequeItemOperation/SetPercentDiscount."""
        return await self._call(self.PATH_SET_PERCENT_DISCOUNT, req, models.UpdateResult)

DocChequeOperationService = ChequeOperationService

__all__ = ['ChequeOperationService', 'DocChequeOperationService']
