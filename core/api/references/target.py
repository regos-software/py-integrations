"""REGOS API service for Target."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class TargetService(RegosAPIService):
    PATH_GET = "Target/Get"
    PATH_ADD = "Target/Add"
    PATH_FINISH = "Target/Finish"
    PATH_DELETE = "Target/Delete"
    PATH_GET_HISTORY = "Target/GetHistory"
    REQUEST_MODELS = {
        'add': models.TargetAdd,
        'delete': models.Base_ID,
        'finish': models.Base_ID,
        'get': models.TargetGet,
        'get_history': models.Base_ID,
    }

    async def get(self, req: models.TargetGet | dict[str, Any]) -> models.TargetRegosArrayResult:
        """POST Target/Get."""
        return await self._call(self.PATH_GET, req, models.TargetRegosArrayResult)

    async def add(self, req: models.TargetAdd | dict[str, Any]) -> models.InsertResult:
        """POST Target/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def finish(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST Target/Finish."""
        return await self._call(self.PATH_FINISH, req, models.UpdateResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST Target/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def get_history(self, req: models.Base_ID | dict[str, Any]) -> models.TargetHistoryRegosObjectResult:
        """POST Target/GetHistory."""
        return await self._call(self.PATH_GET_HISTORY, req, models.TargetHistoryRegosObjectResult)

__all__ = ['TargetService']
