"""REGOS API service for AccountOperationCategory."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class AccountOperationCategoryService(RegosAPIService):
    PATH_GET = "AccountOperationCategory/Get"
    PATH_ADD = "AccountOperationCategory/Add"
    PATH_EDIT = "AccountOperationCategory/Edit"
    PATH_DELETE = "AccountOperationCategory/Delete"
    REQUEST_MODELS = {
        'add': models.AccountOperationCategoryAdd,
        'delete': models.AccountOperationCategoryDelete,
        'edit': models.AccountOperationCategoryEdit,
        'get': models.AccountOperationCategoryGet,
    }

    async def get(self, req: models.AccountOperationCategoryGet | dict[str, Any]) -> models.AccountOperationCategoryRegosOffsettedArrayResult:
        """POST AccountOperationCategory/Get."""
        return await self._call(self.PATH_GET, req, models.AccountOperationCategoryRegosOffsettedArrayResult)

    async def add(self, req: models.AccountOperationCategoryAdd | dict[str, Any]) -> models.InsertResult:
        """POST AccountOperationCategory/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.AccountOperationCategoryEdit | dict[str, Any]) -> models.UpdateResult:
        """POST AccountOperationCategory/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.AccountOperationCategoryDelete | dict[str, Any]) -> models.UpdateResult:
        """POST AccountOperationCategory/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['AccountOperationCategoryService']
