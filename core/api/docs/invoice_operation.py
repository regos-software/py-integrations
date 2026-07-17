"""REGOS API service for InvoiceOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class InvoiceOperationService(RegosAPIService):
    PATH_GET = "InvoiceOperation/Get"
    PATH_ADD = "InvoiceOperation/Add"
    PATH_EDIT = "InvoiceOperation/Edit"
    PATH_DELETE = "InvoiceOperation/Delete"
    PATH_SET_PRICE_BY_PRICE_TYPE = "InvoiceOperation/SetPriceByPriceType"
    PATH_MOVE_OPERATIONS = "InvoiceOperation/MoveOperations"
    PATH_GET_OPERATIONS_FROM_ROAMING = "InvoiceOperation/GetOperationsFromRoaming"
    REQUEST_MODELS = {
        'get': models.InvoiceOperationGet,
        'get_operations_from_roaming': models.InvoiceRoamingOperationGet,
        'move_operations': models.DocsOperationsMovement,
        'set_price_by_price_type': models.SetPriceByPriceType_Model,
    }

    async def get(self, req: models.InvoiceOperationGet | dict[str, Any]) -> models.InvoiceOperationRegosOffsettedArrayResult:
        """POST InvoiceOperation/Get."""
        return await self._call(self.PATH_GET, req, models.InvoiceOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.InvoiceOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST InvoiceOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.InvoiceOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST InvoiceOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.InvoiceOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST InvoiceOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_price_by_price_type(self, req: models.SetPriceByPriceType_Model | dict[str, Any]) -> models.UpdateResult:
        """POST InvoiceOperation/SetPriceByPriceType."""
        return await self._call(self.PATH_SET_PRICE_BY_PRICE_TYPE, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST InvoiceOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

    async def get_operations_from_roaming(self, req: models.InvoiceRoamingOperationGet | dict[str, Any]) -> models.InvoiceRoamingOperationArrayRegosObjectResult:
        """POST InvoiceOperation/GetOperationsFromRoaming."""
        return await self._call(self.PATH_GET_OPERATIONS_FROM_ROAMING, req, models.InvoiceRoamingOperationArrayRegosObjectResult)

__all__ = ['InvoiceOperationService']
