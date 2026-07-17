"""REGOS API service for Deal."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DealService(RegosAPIService):
    PATH_GET = "Deal/Get"
    PATH_ADD = "Deal/Add"
    PATH_EDIT = "Deal/Edit"
    PATH_SET_STAGE = "Deal/SetStage"
    PATH_SET_RESPONSIBLE = "Deal/SetResponsible"
    PATH_SET_PARTICIPANTS = "Deal/SetParticipants"
    PATH_CLOSE = "Deal/Close"
    PATH_DELETE = "Deal/Delete"
    REQUEST_MODELS = {
        'add': models.DealAdd,
        'close': models.DealClose,
        'delete': models.DealDelete,
        'edit': models.DealEdit,
        'get': models.DealGet,
        'set_participants': models.DealSetParticipants,
        'set_responsible': models.DealSetResponsible,
        'set_stage': models.DealSetStage,
    }

    async def get(self, req: models.DealGet | dict[str, Any]) -> models.DealRegosOffsettedArrayResult:
        """POST Deal/Get."""
        return await self._call(self.PATH_GET, req, models.DealRegosOffsettedArrayResult)

    async def add(self, req: models.DealAdd | dict[str, Any]) -> models.InsertResult:
        """POST Deal/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DealEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Deal/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def set_stage(self, req: models.DealSetStage | dict[str, Any]) -> models.UpdateResult:
        """POST Deal/SetStage."""
        return await self._call(self.PATH_SET_STAGE, req, models.UpdateResult)

    async def set_responsible(self, req: models.DealSetResponsible | dict[str, Any]) -> models.UpdateResult:
        """POST Deal/SetResponsible."""
        return await self._call(self.PATH_SET_RESPONSIBLE, req, models.UpdateResult)

    async def set_participants(self, req: models.DealSetParticipants | dict[str, Any]) -> models.UpdateResult:
        """POST Deal/SetParticipants."""
        return await self._call(self.PATH_SET_PARTICIPANTS, req, models.UpdateResult)

    async def close(self, req: models.DealClose | dict[str, Any]) -> models.UpdateResult:
        """POST Deal/Close."""
        return await self._call(self.PATH_CLOSE, req, models.UpdateResult)

    async def delete(self, req: models.DealDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Deal/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DealService']
