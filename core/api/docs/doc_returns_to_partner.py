"""REGOS API service for DocReturnsToPartner."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocReturnsToPartnerService(RegosAPIService):
    PATH_GET = "DocReturnsToPartner/Get"
    PATH_ADD = "DocReturnsToPartner/Add"
    PATH_EDIT = "DocReturnsToPartner/Edit"
    PATH_DELETE_MARK = "DocReturnsToPartner/DeleteMark"
    PATH_DELETE = "DocReturnsToPartner/Delete"
    PATH_LOCK = "DocReturnsToPartner/Lock"
    PATH_UNLOCK = "DocReturnsToPartner/Unlock"
    PATH_PERFORM = "DocReturnsToPartner/Perform"
    PATH_PERFORM_CANCEL = "DocReturnsToPartner/PerformCancel"
    REQUEST_MODELS = {
        'add': models.DocReturnsToPartnerAdd,
        'delete': models.DocReturnsToPartnerDelete,
        'delete_mark': models.DocReturnsToPartnerDeleteMark,
        'edit': models.DocReturnsToPartnerEdit,
        'get': models.DocReturnsToPartnerGet,
        'lock': models.DocReturnsToPartnerLockAndUnlock,
        'perform': models.DocReturnsToPartnerPerformAndCancel,
        'perform_cancel': models.DocReturnsToPartnerPerformAndCancel,
        'unlock': models.DocReturnsToPartnerLockAndUnlock,
    }

    async def get(self, req: models.DocReturnsToPartnerGet | dict[str, Any]) -> models.DocReturnsToPartnerRegosOffsettedArrayResult:
        """POST DocReturnsToPartner/Get."""
        return await self._call(self.PATH_GET, req, models.DocReturnsToPartnerRegosOffsettedArrayResult)

    async def add(self, req: models.DocReturnsToPartnerAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocReturnsToPartner/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocReturnsToPartnerEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocReturnsToPartner/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocReturnsToPartnerDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocReturnsToPartner/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocReturnsToPartnerDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocReturnsToPartner/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def lock(self, req: models.DocReturnsToPartnerLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocReturnsToPartner/Lock."""
        return await self._call(self.PATH_LOCK, req, models.UpdateResult)

    async def unlock(self, req: models.DocReturnsToPartnerLockAndUnlock | dict[str, Any]) -> models.UpdateResult:
        """POST DocReturnsToPartner/Unlock."""
        return await self._call(self.PATH_UNLOCK, req, models.UpdateResult)

    async def perform(self, req: models.DocReturnsToPartnerPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocReturnsToPartner/Perform."""
        return await self._call(self.PATH_PERFORM, req, models.UpdateResult)

    async def perform_cancel(self, req: models.DocReturnsToPartnerPerformAndCancel | dict[str, Any]) -> models.UpdateResult:
        """POST DocReturnsToPartner/PerformCancel."""
        return await self._call(self.PATH_PERFORM_CANCEL, req, models.UpdateResult)

__all__ = ['DocReturnsToPartnerService']
