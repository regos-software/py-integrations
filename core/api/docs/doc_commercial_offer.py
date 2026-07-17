"""REGOS API service for DocCommercialOffer."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocCommercialOfferService(RegosAPIService):
    PATH_GET = "DocCommercialOffer/Get"
    PATH_ADD = "DocCommercialOffer/Add"
    PATH_EDIT = "DocCommercialOffer/Edit"
    PATH_DELETE_MARK = "DocCommercialOffer/DeleteMark"
    PATH_DELETE = "DocCommercialOffer/Delete"
    PATH_LOCK = "DocCommercialOffer/Lock"
    PATH_UNLOCK = "DocCommercialOffer/Unlock"
    REQUEST_MODELS = {
        'add': models.DocCommercialOfferAdd,
        'delete': models.DocCommercialOfferDelete,
        'delete_mark': models.DocCommercialOfferDeleteMark,
        'edit': models.DocCommercialOfferEdit,
        'get': models.DocCommercialOfferGet,
        'lock': models.DocCommercialOfferLockAndUnlock,
        'unlock': models.DocCommercialOfferLockAndUnlock,
    }

    async def get(self, req: models.DocCommercialOfferGet | dict[str, Any]) -> models.DocCommercialOfferRegosOffsettedArrayResult:
        """POST DocCommercialOffer/Get."""
        return await self._call(self.PATH_GET, req, models.DocCommercialOfferRegosOffsettedArrayResult)

    async def add(self, req: models.DocCommercialOfferAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocCommercialOffer/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocCommercialOfferEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocCommercialOffer/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocCommercialOfferDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocCommercialOffer/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocCommercialOfferDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocCommercialOffer/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocCommercialOfferLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocCommercialOffer/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocCommercialOfferLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocCommercialOffer/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

__all__ = ['DocCommercialOfferService']
