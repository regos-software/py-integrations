"""REGOS API service for DocOrderFromPartner."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocOrderFromPartnerService(RegosAPIService):
    PATH_GET = "DocOrderFromPartner/Get"
    PATH_ADD = "DocOrderFromPartner/Add"
    PATH_EDIT = "DocOrderFromPartner/Edit"
    PATH_DELETE_MARK = "DocOrderFromPartner/DeleteMark"
    PATH_DELETE = "DocOrderFromPartner/Delete"
    PATH_LOCK = "DocOrderFromPartner/Lock"
    PATH_UNLOCK = "DocOrderFromPartner/Unlock"
    REQUEST_MODELS = {
        'add': models.DocOrderFromPartnerAdd,
        'delete': models.DocOrderFromPartnerDelete,
        'delete_mark': models.DocOrderFromPartnerDeleteMark,
        'edit': models.DocOrderFromPartnerEdit,
        'get': models.DocOrderFromPartnerGet,
        'lock': models.DocOrderFromPartnerLockAndUnlock,
        'unlock': models.DocOrderFromPartnerLockAndUnlock,
    }

    async def get(self, req: models.DocOrderFromPartnerGet | dict[str, Any]) -> models.DocOrderFromPartnerRegosOffsettedArrayResult:
        """POST DocOrderFromPartner/Get."""
        return await self._call(self.PATH_GET, req, models.DocOrderFromPartnerRegosOffsettedArrayResult)

    async def add(self, req: models.DocOrderFromPartnerAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocOrderFromPartner/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocOrderFromPartnerEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderFromPartner/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocOrderFromPartnerDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderFromPartner/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocOrderFromPartnerDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderFromPartner/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocOrderFromPartnerLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderFromPartner/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocOrderFromPartnerLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocOrderFromPartner/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

__all__ = ['DocOrderFromPartnerService']
