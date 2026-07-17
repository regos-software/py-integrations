"""REGOS API service for Currency."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class CurrencyService(RegosAPIService):
    PATH_GET = "Currency/Get"
    PATH_ADD = "Currency/Add"
    PATH_EDIT = "Currency/Edit"
    PATH_DELETE = "Currency/Delete"
    PATH_EDIT_EXCHANGE_RATE = "Currency/EditExchangeRate"
    REQUEST_MODELS = {
        'add': models.CurrencyAdd,
        'delete': models.CurrencyDelete,
        'edit': models.CurrencyEdit,
        'edit_exchange_rate': models.CurrencyEditExchangeRate,
        'get': models.CurrencyGet,
    }

    async def get(self, req: models.CurrencyGet | dict[str, Any]) -> models.CurrencyRegosOffsettedArrayResult:
        """POST Currency/Get."""
        return await self._call(self.PATH_GET, req, models.CurrencyRegosOffsettedArrayResult)

    async def add(self, req: models.CurrencyAdd | dict[str, Any]) -> models.InsertResult:
        """POST Currency/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.CurrencyEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Currency/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.CurrencyDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Currency/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def edit_exchange_rate(self, req: models.CurrencyEditExchangeRate | dict[str, Any]) -> models.UpdateResult:
        """POST Currency/EditExchangeRate."""
        return await self._call(self.PATH_EDIT_EXCHANGE_RATE, req, models.UpdateResult)

__all__ = ['CurrencyService']
