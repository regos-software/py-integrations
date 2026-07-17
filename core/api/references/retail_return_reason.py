"""REGOS API service for RetailReturnReason."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RetailReturnReasonService(RegosAPIService):
    PATH_GET = "RetailReturnReason/Get"
    PATH_ADD = "RetailReturnReason/Add"
    PATH_EDIT = "RetailReturnReason/Edit"
    PATH_DELETE = "RetailReturnReason/Delete"
    REQUEST_MODELS = {
        'add': models.RetailReturnReasonAdd,
        'delete': models.RetailReturnReasonDelete,
        'edit': models.RetailReturnReasonEdit,
        'get': models.RetailReturnReasonGet,
    }

    async def get(self, req: models.RetailReturnReasonGet | dict[str, Any]) -> models.RetailReturnReasonRegosOffsettedArrayResult:
        """POST RetailReturnReason/Get."""
        return await self._call(self.PATH_GET, req, models.RetailReturnReasonRegosOffsettedArrayResult)

    async def add(self, req: models.RetailReturnReasonAdd | dict[str, Any]) -> models.InsertResult:
        """POST RetailReturnReason/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.RetailReturnReasonEdit | dict[str, Any]) -> models.UpdateResult:
        """POST RetailReturnReason/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.RetailReturnReasonDelete | dict[str, Any]) -> models.UpdateResult:
        """POST RetailReturnReason/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['RetailReturnReasonService']
