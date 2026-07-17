"""REGOS API service for Account."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class AccountService(RegosAPIService):
    PATH_GET = "Account/Get"
    PATH_ADD = "Account/Add"
    PATH_EDIT = "Account/Edit"
    PATH_DELETE = "Account/Delete"
    REQUEST_MODELS = {
        'add': models.AccountAdd,
        'delete': models.AccountDelete,
        'edit': models.AccountEdit,
        'get': models.AccountGet,
    }

    async def get(self, req: models.AccountGet | dict[str, Any]) -> models.AccountRegosOffsettedArrayResult:
        """POST Account/Get."""
        return await self._call(self.PATH_GET, req, models.AccountRegosOffsettedArrayResult)

    async def add(self, req: models.AccountAdd | dict[str, Any]) -> models.InsertResult:
        """POST Account/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.AccountEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Account/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.AccountDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Account/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['AccountService']
