"""REGOS API service for RetailCard."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RetailCardService(RegosAPIService):
    PATH_GET = "RetailCard/Get"
    PATH_ADD = "RetailCard/Add"
    PATH_EDIT = "RetailCard/Edit"
    PATH_DELETE = "RetailCard/Delete"
    PATH_ADD_WITH_CUSTOMER = "RetailCard/AddWithCustomer"
    PATH_GET_BALANCE = "RetailCard/GetBalance"
    PATH_GET_OPERATIONS = "RetailCard/GetOperations"
    PATH_GET_MIGRATION_HISTORY = "RetailCard/GetMigrationHistory"
    REQUEST_MODELS = {
        'add': models.RetailCardAdd,
        'add_with_customer': models.RetailCardAddWithCustomer,
        'delete': models.RetailCardDelete,
        'edit': models.RetailCardEdit,
        'get': models.RetailCardGet,
        'get_balance': models.PromoBonusesRemainderGet,
        'get_migration_history': models.RetailCardMigrationHistoryGet,
        'get_operations': models.RetailCardOperationGet,
    }

    async def get(self, req: models.RetailCardGet | dict[str, Any]) -> models.RetailCardRegosOffsettedArrayResult:
        """POST RetailCard/Get."""
        return await self._call(self.PATH_GET, req, models.RetailCardRegosOffsettedArrayResult)

    async def add(self, req: models.RetailCardAdd | dict[str, Any]) -> models.InsertResult:
        """POST RetailCard/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.RetailCardEdit | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCard/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.RetailCardDelete | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCard/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def add_with_customer(self, req: models.RetailCardAddWithCustomer | dict[str, Any]) -> models.RetailCardRegosObjectResult:
        """POST RetailCard/AddWithCustomer."""
        return await self._call(self.PATH_ADD_WITH_CUSTOMER, req, models.RetailCardRegosObjectResult)

    async def get_balance(self, req: models.PromoBonusesRemainderGet | dict[str, Any]) -> models.PromoBonusesRemainderRegosObjectResult:
        """POST RetailCard/GetBalance."""
        return await self._call(self.PATH_GET_BALANCE, req, models.PromoBonusesRemainderRegosObjectResult)

    async def get_operations(self, req: models.RetailCardOperationGet | dict[str, Any]) -> models.RetailCardOperationRegosOffsettedArrayResult:
        """POST RetailCard/GetOperations."""
        return await self._call(self.PATH_GET_OPERATIONS, req, models.RetailCardOperationRegosOffsettedArrayResult)

    async def get_migration_history(self, req: models.RetailCardMigrationHistoryGet | dict[str, Any]) -> models.RetailCardMigrationHistoryRegosArrayResult:
        """POST RetailCard/GetMigrationHistory."""
        return await self._call(self.PATH_GET_MIGRATION_HISTORY, req, models.RetailCardMigrationHistoryRegosArrayResult)

__all__ = ['RetailCardService']
