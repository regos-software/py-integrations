"""REGOS API service for ItemImage."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ItemImageService(RegosAPIService):
    PATH_GET = "ItemImage/Get"
    PATH_SAVE = "ItemImage/Save"
    PATH_DELETE = "ItemImage/Delete"
    REQUEST_MODELS = {
        'delete': models.ItemImageDelete,
        'get': models.ItemImageGet,
    }

    async def get(self, req: models.ItemImageGet | dict[str, Any]) -> models.ItemImageRegosArrayResult:
        """POST ItemImage/Get."""
        return await self._call(self.PATH_GET, req, models.ItemImageRegosArrayResult)

    async def save(self, body: dict[str, Any] | None = None) -> models.InsertResult:
        """POST ItemImage/Save."""
        return await self._call(self.PATH_SAVE, body or {}, models.InsertResult)

    async def delete(self, req: models.ItemImageDelete | dict[str, Any]) -> models.UpdateResult:
        """POST ItemImage/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['ItemImageService']
