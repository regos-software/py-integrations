"""REGOS API service for SetPriceOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class SetPriceOperationService(RegosAPIService):
    PATH_GET = "SetPriceOperation/Get"
    PATH_ADD = "SetPriceOperation/Add"
    PATH_EDIT = "SetPriceOperation/Edit"
    PATH_DELETE = "SetPriceOperation/Delete"
    PATH_COPY_OPERATIONS_FROM_DOC_PURCHASE = "SetPriceOperation/CopyOperationsFromDocPurchase"
    PATH_SET_BASE_PRICE_BY_PRICE_TYPE = "SetPriceOperation/SetBasePriceByPriceType"
    PATH_SET_NEW_PRICE_BY_PRICE_TYPE = "SetPriceOperation/SetNewPriceByPriceType"
    REQUEST_MODELS = {
        'copy_operations_from_doc_purchase': models.DocsOperationsCopy,
        'get': models.SetPriceOperationGet,
        'set_base_price_by_price_type': models.SetPriceByPriceType_Model,
        'set_new_price_by_price_type': models.SetPriceByPriceType_Model,
    }

    async def get(self, req: models.SetPriceOperationGet | dict[str, Any]) -> models.SetPriceOperationRegosOffsettedArrayResult:
        """POST SetPriceOperation/Get."""
        return await self._call(self.PATH_GET, req, models.SetPriceOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.SetPriceOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST SetPriceOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.SetPriceOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST SetPriceOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.SetPriceOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST SetPriceOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def copy_operations_from_doc_purchase(self, req: models.DocsOperationsCopy | dict[str, Any]) -> models.ObjectRegosObjectResult:
        """POST SetPriceOperation/CopyOperationsFromDocPurchase."""
        return await self._call(self.PATH_COPY_OPERATIONS_FROM_DOC_PURCHASE, req, models.ObjectRegosObjectResult)

    async def set_base_price_by_price_type(self, req: models.SetPriceByPriceType_Model | dict[str, Any]) -> models.UpdateResult:
        """POST SetPriceOperation/SetBasePriceByPriceType."""
        return await self._call(self.PATH_SET_BASE_PRICE_BY_PRICE_TYPE, req, models.UpdateResult)

    async def set_new_price_by_price_type(self, req: models.SetPriceByPriceType_Model | dict[str, Any]) -> models.UpdateResult:
        """POST SetPriceOperation/SetNewPriceByPriceType."""
        return await self._call(self.PATH_SET_NEW_PRICE_BY_PRICE_TYPE, req, models.UpdateResult)

__all__ = ['SetPriceOperationService']
