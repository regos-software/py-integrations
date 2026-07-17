"""REGOS API service for FastItem."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class FastItemService(RegosAPIService):
    PATH_GET = "pos/FastItem/Get"
    PATH_ADD = "pos/FastItem/Add"
    PATH_DELETE = "pos/FastItem/Delete"
    REQUEST_MODELS = {
        'add': models.RegosOnlineFastItemAdd,
        'delete': models.Base_ID,
        'get': models.RegosOnlineFastItemGet,
    }

    async def get(self, req: models.RegosOnlineFastItemGet | dict[str, Any]) -> models.RegosOnlineFastItemArrayRegosObjectResult:
        """POST pos/FastItem/Get."""
        return await self._call(self.PATH_GET, req, models.RegosOnlineFastItemArrayRegosObjectResult)

    async def add(self, req: models.RegosOnlineFastItemAdd | dict[str, Any]) -> models.InsertResult:
        """POST pos/FastItem/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.SingleObjectResult:
        """POST pos/FastItem/Delete."""
        return await self._call(self.PATH_DELETE, req, models.SingleObjectResult)

__all__ = ['FastItemService']
