"""REGOS API service for CashServer."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class CashServerService(RegosAPIService):
    PATH_GET = "CashServer/Get"
    PATH_ADD = "CashServer/Add"
    PATH_EDIT = "CashServer/Edit"
    PATH_DELETE = "CashServer/Delete"
    PATH_BEGIN_SYNC = "CashServer/BeginSync"
    PATH_END_SYNC = "CashServer/EndSync"
    REQUEST_MODELS = {
        'add': models.CashServerAdd,
        'begin_sync': models.CashServerOnlyId,
        'delete': models.CashServerOnlyId,
        'edit': models.CashServerEdit,
        'end_sync': models.CashServerOnlyId,
        'get': models.CashServerGet,
    }

    async def get(self, req: models.CashServerGet | dict[str, Any]) -> models.CashServerArrayRegosObjectResult:
        """POST CashServer/Get."""
        return await self._call(self.PATH_GET, req, models.CashServerArrayRegosObjectResult)

    async def add(self, req: models.CashServerAdd | dict[str, Any]) -> models.InsertResult:
        """POST CashServer/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.CashServerEdit | dict[str, Any]) -> models.UpdateResult:
        """POST CashServer/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.CashServerOnlyId | dict[str, Any]) -> models.UpdateResult:
        """POST CashServer/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def begin_sync(self, req: models.CashServerOnlyId | dict[str, Any]) -> models.StartSyncDatetimeRegosObjectResult:
        """POST CashServer/BeginSync."""
        return await self._call(self.PATH_BEGIN_SYNC, req, models.StartSyncDatetimeRegosObjectResult)

    async def end_sync(self, req: models.CashServerOnlyId | dict[str, Any]) -> models.EndSyncDatetimeRegosObjectResult:
        """POST CashServer/EndSync."""
        return await self._call(self.PATH_END_SYNC, req, models.EndSyncDatetimeRegosObjectResult)

__all__ = ['CashServerService']
