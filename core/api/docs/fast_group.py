"""REGOS API service for FastGroup."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class FastGroupService(RegosAPIService):
    PATH_GET = "pos/FastGroup/Get"
    PATH_ADD = "pos/FastGroup/Add"
    PATH_EDIT = "pos/FastGroup/Edit"
    PATH_DELETE = "pos/FastGroup/Delete"
    REQUEST_MODELS = {
        'add': models.RegosOnlineFastGroupAdd,
        'delete': models.Base_ID,
        'edit': models.RegosOnlineFastGroupEdit,
        'get': models.RegosOnlineFastGroupGet,
    }

    async def get(self, req: models.RegosOnlineFastGroupGet | dict[str, Any]) -> models.RegosOnlineFastGroupArrayRegosObjectResult:
        """POST pos/FastGroup/Get."""
        return await self._call(self.PATH_GET, req, models.RegosOnlineFastGroupArrayRegosObjectResult)

    async def add(self, req: models.RegosOnlineFastGroupAdd | dict[str, Any]) -> models.InsertResult:
        """POST pos/FastGroup/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.RegosOnlineFastGroupEdit | dict[str, Any]) -> models.SingleObjectResult:
        """POST pos/FastGroup/Edit."""
        return await self._call(self.PATH_EDIT, req, models.SingleObjectResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.SingleObjectResult:
        """POST pos/FastGroup/Delete."""
        return await self._call(self.PATH_DELETE, req, models.SingleObjectResult)

__all__ = ['FastGroupService']
