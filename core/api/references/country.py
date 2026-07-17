"""REGOS API service for Country."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class CountryService(RegosAPIService):
    PATH_GET = "Country/Get"
    PATH_ADD = "Country/Add"
    PATH_EDIT = "Country/Edit"
    PATH_DELETE = "Country/Delete"
    REQUEST_MODELS = {
        'add': models.CountryAdd,
        'delete': models.CountryDelete,
        'edit': models.CountryEdit,
        'get': models.CountryGet,
    }

    async def get(self, req: models.CountryGet | dict[str, Any]) -> models.CountryRegosOffsettedArrayResult:
        """POST Country/Get."""
        return await self._call(self.PATH_GET, req, models.CountryRegosOffsettedArrayResult)

    async def add(self, req: models.CountryAdd | dict[str, Any]) -> models.InsertResult:
        """POST Country/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.CountryEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Country/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.CountryDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Country/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['CountryService']
