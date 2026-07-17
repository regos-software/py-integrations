"""REGOS API service for Client."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ClientService(RegosAPIService):
    PATH_GET = "Client/Get"
    PATH_ADD = "Client/Add"
    PATH_EDIT = "Client/Edit"
    PATH_DELETE = "Client/Delete"
    PATH_SET_RESPONSIBLE = "Client/SetResponsible"
    PATH_MERGE = "Client/Merge"
    REQUEST_MODELS = {
        'add': models.ClientAdd,
        'delete': models.ClientDelete,
        'edit': models.ClientEdit,
        'get': models.ClientGet,
        'merge': models.ClientMerge,
        'set_responsible': models.ClientSetResponsible,
    }

    async def get(self, req: models.ClientGet | dict[str, Any]) -> models.ClientRegosOffsettedArrayResult:
        """POST Client/Get."""
        return await self._call(self.PATH_GET, req, models.ClientRegosOffsettedArrayResult)

    async def add(self, req: models.ClientAdd | dict[str, Any]) -> models.InsertResult:
        """POST Client/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.ClientEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Client/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.ClientDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Client/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_responsible(self, req: models.ClientSetResponsible | dict[str, Any]) -> models.UpdateResult:
        """POST Client/SetResponsible."""
        return await self._call(self.PATH_SET_RESPONSIBLE, req, models.UpdateResult)

    async def merge(self, req: models.ClientMerge | dict[str, Any]) -> models.UpdateResult:
        """POST Client/Merge."""
        return await self._call(self.PATH_MERGE, req, models.UpdateResult)

__all__ = ['ClientService']
