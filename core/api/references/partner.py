"""REGOS API service for Partner."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PartnerService(RegosAPIService):
    PATH_GET = "Partner/Get"
    PATH_ADD = "Partner/Add"
    PATH_EDIT = "Partner/Edit"
    PATH_DELETE_MARK = "Partner/DeleteMark"
    PATH_DELETE = "Partner/Delete"
    PATH_GET_CURRENT_BALANCE = "Partner/GetCurrentBalance"
    REQUEST_MODELS = {
        'add': models.PartnerAdd,
        'delete': models.PartnerDelete,
        'delete_mark': models.PartnerDeleteMark,
        'edit': models.PartnerEdit,
        'get': models.PartnerGet,
        'get_current_balance': models.PartnerCurrentBalanceGet,
    }

    async def get(self, req: models.PartnerGet | dict[str, Any]) -> models.PartnerRegosOffsettedArrayResult:
        """POST Partner/Get."""
        return await self._call(self.PATH_GET, req, models.PartnerRegosOffsettedArrayResult)

    async def add(self, req: models.PartnerAdd | dict[str, Any]) -> models.InsertResult:
        """POST Partner/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.PartnerEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Partner/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.PartnerDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST Partner/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.PartnerDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Partner/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def get_current_balance(self, req: models.PartnerCurrentBalanceGet | dict[str, Any]) -> models.DecimalRegosObjectResult:
        """POST Partner/GetCurrentBalance."""
        return await self._call(self.PATH_GET_CURRENT_BALANCE, req, models.DecimalRegosObjectResult)

__all__ = ['PartnerService']
