"""REGOS API service for DocOrderToPartner."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocOrderToPartnerService(RegosAPIService):
    PATH_GET = "DocOrderToPartner/Get"
    PATH_ADD = "DocOrderToPartner/Add"
    PATH_EDIT = "DocOrderToPartner/Edit"
    PATH_DELETE_MARK = "DocOrderToPartner/DeleteMark"
    PATH_DELETE = "DocOrderToPartner/Delete"
    PATH_LOCK = "DocOrderToPartner/Lock"
    PATH_UNLOCK = "DocOrderToPartner/Unlock"
    REQUEST_MODELS = {
        'add': models.DocOrderToPartnerAdd,
        'delete': models.DocOrderToPartnerDelete,
        'delete_mark': models.DocOrderToPartnerDeleteMark,
        'edit': models.DocOrderToPartnerEdit,
        'get': models.DocOrderToPartnerGet,
        'lock': models.DocOrderToPartnerLockAndUnlock,
        'unlock': models.DocOrderToPartnerLockAndUnlock,
    }

    async def get(self, req: models.DocOrderToPartnerGet | dict[str, Any]) -> models.DocOrderToPartnerRegosOffsettedArrayResult:
        """POST DocOrderToPartner/Get."""
        return await self._call(self.PATH_GET, req, models.DocOrderToPartnerRegosOffsettedArrayResult)

    async def add(self, req: models.DocOrderToPartnerAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocOrderToPartner/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocOrderToPartnerEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToPartner/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocOrderToPartnerDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToPartner/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocOrderToPartnerDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToPartner/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocOrderToPartnerLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToPartner/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocOrderToPartnerLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderToPartner/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

__all__ = ['DocOrderToPartnerService']
