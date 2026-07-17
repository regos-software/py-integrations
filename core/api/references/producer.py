"""REGOS API service for Producer."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ProducerService(RegosAPIService):
    PATH_GET = "Producer/Get"
    PATH_ADD = "Producer/Add"
    PATH_EDIT = "Producer/Edit"
    PATH_DELETE = "Producer/Delete"
    REQUEST_MODELS = {
        'add': models.ProducerAdd,
        'delete': models.ProducerDelete,
        'edit': models.ProducerEdit,
        'get': models.ProducerGet,
    }

    async def get(self, req: models.ProducerGet | dict[str, Any]) -> models.ProducerRegosOffsettedArrayResult:
        """POST Producer/Get."""
        return await self._call(self.PATH_GET, req, models.ProducerRegosOffsettedArrayResult)

    async def add(self, req: models.ProducerAdd | dict[str, Any]) -> models.InsertResult:
        """POST Producer/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.ProducerEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Producer/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.ProducerDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Producer/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['ProducerService']
