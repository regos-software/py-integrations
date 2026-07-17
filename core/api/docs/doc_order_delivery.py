"""REGOS API service for DocOrderDelivery."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocOrderDeliveryService(RegosAPIService):
    PATH_GET = "DocOrderDelivery/Get"
    PATH_GET_COUNT = "DocOrderDelivery/GetCount"
    PATH_ADD = "DocOrderDelivery/Add"
    PATH_ADD_FULL = "DocOrderDelivery/AddFull"
    PATH_EDIT = "DocOrderDelivery/Edit"
    PATH_DELETE_MARK = "DocOrderDelivery/DeleteMark"
    PATH_DELETE = "DocOrderDelivery/Delete"
    PATH_LOCK = "DocOrderDelivery/Lock"
    PATH_UNLOCK = "DocOrderDelivery/Unlock"
    PATH_SET_STATUS = "DocOrderDelivery/SetStatus"
    PATH_SET_FISCAL_INFO = "DocOrderDelivery/SetFiscalInfo"
    PATH_TO_BEGINNING = "DocOrderDelivery/ToBeginning"
    PATH_SET_STOCK = "DocOrderDelivery/SetStock"
    PATH_SET_OPERATING_CASH = "DocOrderDelivery/SetOperatingCash"
    PATH_SET_COURIER = "DocOrderDelivery/SetCourier"
    PATH_SET_RETAIL_CARD = "DocOrderDelivery/SetRetailCard"
    PATH_RETURN_ = "DocOrderDelivery/Return"
    PATH_ACTUALIZE = "DocOrderDelivery/Actualize"
    REQUEST_MODELS = {
        'actualize': models.DocOrderDeliveryActualize,
        'add': models.DocOrderDeliveryAdd,
        'add_full': models.DocOrderDeliveryAddFull,
        'delete': models.DocOrderDeliveryDelete,
        'delete_mark': models.DocOrderDeliveryDeleteMark,
        'edit': models.DocOrderDeliveryEdit,
        'get': models.DocOrderDeliveryGet,
        'get_count': models.DocOrderDeliveryGet,
        'lock': models.DocOrderDeliveryLockAndUnlock,
        'return_': models.DocOrderDeliveryReturnProcessing,
        'set_courier': models.DocOrderDelivery_SetCourier,
        'set_fiscal_info': models.DocOrderDelivery_SetFiscalInfo,
        'set_operating_cash': models.DocOrderDelivery_SetOperatingCash,
        'set_retail_card': models.DocOrderDelivery_SetRetailCard,
        'set_status': models.DocOrderDelivery_SetStatus,
        'set_stock': models.DocOrderDeliverySetStock,
        'to_beginning': models.DocOrderDelivery_Beginning,
        'unlock': models.DocOrderDeliveryLockAndUnlock,
    }

    async def get(self, req: models.DocOrderDeliveryGet | dict[str, Any]) -> models.DocOrderDeliveryRegosOffsettedArrayResult:
        """POST DocOrderDelivery/Get."""
        return await self._call(self.PATH_GET, req, models.DocOrderDeliveryRegosOffsettedArrayResult)

    async def get_count(self, req: models.DocOrderDeliveryGet | dict[str, Any]) -> models.Int64RegosObjectResult:
        """POST DocOrderDelivery/GetCount."""
        return await self._call(self.PATH_GET_COUNT, req, models.Int64RegosObjectResult)

    async def add(self, req: models.DocOrderDeliveryAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocOrderDelivery/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def add_full(self, req: models.DocOrderDeliveryAddFull | dict[str, Any]) -> models.InsertResult:
        """POST DocOrderDelivery/AddFull."""
        return await self._call(self.PATH_ADD_FULL, req, models.InsertResult)

    async def edit(self, req: models.DocOrderDeliveryEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocOrderDeliveryDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocOrderDeliveryDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocOrderDeliveryLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocOrderDeliveryLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def set_status(self, req: models.DocOrderDelivery_SetStatus | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/SetStatus."""
        return await self._call(self.PATH_SET_STATUS, req, models.UpdateResult)

    async def set_fiscal_info(self, req: models.DocOrderDelivery_SetFiscalInfo | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/SetFiscalInfo."""
        return await self._call(self.PATH_SET_FISCAL_INFO, req, models.UpdateResult)

    async def to_beginning(self, req: models.DocOrderDelivery_Beginning | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/ToBeginning."""
        return await self._call(self.PATH_TO_BEGINNING, req, models.UpdateResult)

    async def set_stock(self, req: models.DocOrderDeliverySetStock | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/SetStock."""
        return await self._call(self.PATH_SET_STOCK, req, models.UpdateResult)

    async def set_operating_cash(self, req: models.DocOrderDelivery_SetOperatingCash | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/SetOperatingCash."""
        return await self._call(self.PATH_SET_OPERATING_CASH, req, models.UpdateResult)

    async def set_courier(self, req: models.DocOrderDelivery_SetCourier | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/SetCourier."""
        return await self._call(self.PATH_SET_COURIER, req, models.UpdateResult)

    async def set_retail_card(self, req: models.DocOrderDelivery_SetRetailCard | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/SetRetailCard."""
        return await self._call(self.PATH_SET_RETAIL_CARD, req, models.UpdateResult)

    async def return_(self, req: models.DocOrderDeliveryReturnProcessing | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/Return."""
        return await self._call(self.PATH_RETURN_, req, models.UpdateResult)

    async def actualize(self, req: models.DocOrderDeliveryActualize | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderDelivery/Actualize."""
        return await self._call(self.PATH_ACTUALIZE, req, models.UpdateResult)

__all__ = ['DocOrderDeliveryService']
