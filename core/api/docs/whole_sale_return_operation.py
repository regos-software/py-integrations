"""REGOS API service for WholeSaleReturnOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class WholeSaleReturnOperationService(RegosAPIService):
    PATH_GET = "WholeSaleReturnOperation/Get"
    PATH_ADD = "WholeSaleReturnOperation/Add"
    PATH_EDIT = "WholeSaleReturnOperation/Edit"
    PATH_DELETE = "WholeSaleReturnOperation/Delete"
    PATH_GET_DISCOUNT = "WholeSaleReturnOperation/GetDiscount"
    PATH_ADD_DISCOUNT = "WholeSaleReturnOperation/AddDiscount"
    PATH_DELETE_DISCOUNT = "WholeSaleReturnOperation/DeleteDiscount"
    PATH_MOVE_OPRERATIONS = "WholeSaleReturnOperation/moveOprerations"
    REQUEST_MODELS = {
        'add_discount': models.DiscountOperationAdd,
        'delete_discount': models.DiscountOperationDelete,
        'get': models.WholeSaleReturnOperationGet,
        'get_discount': models.DiscountOperationGet,
        'move_oprerations': models.DocsOperationsMovement,
    }

    async def get(self, req: models.WholeSaleReturnOperationGet | dict[str, Any]) -> models.WholeSaleReturnOperationRegosOffsettedArrayResult:
        """POST WholeSaleReturnOperation/Get."""
        return await self._call(self.PATH_GET, req, models.WholeSaleReturnOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.WholeSaleReturnOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST WholeSaleReturnOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.WholeSaleReturnOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST WholeSaleReturnOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.WholeSaleReturnOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST WholeSaleReturnOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def get_discount(self, req: models.DiscountOperationGet | dict[str, Any]) -> models.DiscountOperationRegosArrayResult:
        """POST WholeSaleReturnOperation/GetDiscount."""
        return await self._call(self.PATH_GET_DISCOUNT, req, models.DiscountOperationRegosArrayResult)

    async def add_discount(self, req: models.DiscountOperationAdd | dict[str, Any]) -> models.UpdateResult:
        """POST WholeSaleReturnOperation/AddDiscount."""
        return await self._call(self.PATH_ADD_DISCOUNT, req, models.UpdateResult)

    async def delete_discount(self, req: models.DiscountOperationDelete | dict[str, Any]) -> models.UpdateResult:
        """POST WholeSaleReturnOperation/DeleteDiscount."""
        return await self._call(self.PATH_DELETE_DISCOUNT, req, models.UpdateResult)

    async def move_oprerations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST WholeSaleReturnOperation/moveOprerations."""
        return await self._call(self.PATH_MOVE_OPRERATIONS, req, models.UpdateResult)

__all__ = ['WholeSaleReturnOperationService']
