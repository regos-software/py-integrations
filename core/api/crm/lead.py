"""REGOS API service for Lead."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class LeadService(RegosAPIService):
    PATH_GET = "Lead/Get"
    PATH_ADD = "Lead/Add"
    PATH_EDIT = "Lead/Edit"
    PATH_SET_STAGE = "Lead/SetStage"
    PATH_SET_RESPONSIBLE = "Lead/SetResponsible"
    PATH_SET_PARTICIPANTS = "Lead/SetParticipants"
    PATH_CLOSE = "Lead/Close"
    PATH_DELETE = "Lead/Delete"
    PATH_CONVERT = "Lead/Convert"
    REQUEST_MODELS = {
        'add': models.LeadAdd,
        'close': models.LeadClose,
        'convert': models.LeadConvert,
        'delete': models.LeadDelete,
        'edit': models.LeadEdit,
        'get': models.LeadGet,
        'set_participants': models.LeadSetParticipants,
        'set_responsible': models.LeadSetResponsible,
        'set_stage': models.LeadSetStage,
    }

    async def get(self, req: models.LeadGet | dict[str, Any]) -> models.LeadRegosOffsettedArrayResult:
        """POST Lead/Get."""
        return await self._call(self.PATH_GET, req, models.LeadRegosOffsettedArrayResult)

    async def add(self, req: models.LeadAdd | dict[str, Any]) -> models.InsertResult:
        """POST Lead/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.LeadEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Lead/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def set_stage(self, req: models.LeadSetStage | dict[str, Any]) -> models.UpdateResult:
        """POST Lead/SetStage."""
        return await self._call(self.PATH_SET_STAGE, req, models.UpdateResult)

    async def set_responsible(self, req: models.LeadSetResponsible | dict[str, Any]) -> models.UpdateResult:
        """POST Lead/SetResponsible."""
        return await self._call(self.PATH_SET_RESPONSIBLE, req, models.UpdateResult)

    async def set_participants(self, req: models.LeadSetParticipants | dict[str, Any]) -> models.UpdateResult:
        """POST Lead/SetParticipants."""
        return await self._call(self.PATH_SET_PARTICIPANTS, req, models.UpdateResult)

    async def close(self, req: models.LeadClose | dict[str, Any]) -> models.UpdateResult:
        """POST Lead/Close."""
        return await self._call(self.PATH_CLOSE, req, models.UpdateResult)

    async def delete(self, req: models.LeadDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Lead/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def convert(self, req: models.LeadConvert | dict[str, Any]) -> models.InsertResult:
        """POST Lead/Convert."""
        return await self._call(self.PATH_CONVERT, req, models.InsertResult)

__all__ = ['LeadService']
