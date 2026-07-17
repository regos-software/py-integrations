"""REGOS API service for RetailCustomerGroup."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RetailCustomerGroupService(RegosAPIService):
    PATH_GET = "RetailCustomerGroup/Get"
    PATH_ADD = "RetailCustomerGroup/Add"
    PATH_EDIT = "RetailCustomerGroup/Edit"
    PATH_DELETE = "RetailCustomerGroup/Delete"
    REQUEST_MODELS = {
        'add': models.RetailCustomerGroupAdd,
        'delete': models.RetailCustomerGroupDelete,
        'edit': models.RetailCustomerGroupEdit,
        'get': models.RetailCustomerGroupGet,
    }

    async def get(self, req: models.RetailCustomerGroupGet | dict[str, Any]) -> models.RetailCustomerGroupArrayRegosObjectResult:
        """POST RetailCustomerGroup/Get."""
        return await self._call(self.PATH_GET, req, models.RetailCustomerGroupArrayRegosObjectResult)

    async def add(self, req: models.RetailCustomerGroupAdd | dict[str, Any]) -> models.InsertResult:
        """POST RetailCustomerGroup/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.RetailCustomerGroupEdit | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCustomerGroup/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.RetailCustomerGroupDelete | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCustomerGroup/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['RetailCustomerGroupService']
