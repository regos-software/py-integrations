"""REGOS API service for Channel."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ChannelService(RegosAPIService):
    PATH_GET = "Channel/Get"
    PATH_ADD = "Channel/Add"
    PATH_EDIT = "Channel/Edit"
    PATH_DELETE = "Channel/Delete"
    PATH_SET_OPERATORS = "Channel/SetOperators"
    PATH_SET_INTERVALS = "Channel/SetIntervals"
    REQUEST_MODELS = {
        'add': models.ChannelAdd,
        'delete': models.ChannelDelete,
        'edit': models.ChannelEdit,
        'get': models.ChannelGet,
        'set_intervals': models.ChannelSetIntervals,
        'set_operators': models.ChannelSetOperators,
    }

    async def get(self, req: models.ChannelGet | dict[str, Any]) -> models.ChannelRegosOffsettedArrayResult:
        """POST Channel/Get."""
        return await self._call(self.PATH_GET, req, models.ChannelRegosOffsettedArrayResult)

    async def add(self, req: models.ChannelAdd | dict[str, Any]) -> models.InsertResult:
        """POST Channel/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.ChannelEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Channel/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.ChannelDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Channel/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_operators(self, req: models.ChannelSetOperators | dict[str, Any]) -> models.UpdateResult:
        """POST Channel/SetOperators."""
        return await self._call(self.PATH_SET_OPERATORS, req, models.UpdateResult)

    async def set_intervals(self, req: models.ChannelSetIntervals | dict[str, Any]) -> models.UpdateResult:
        """POST Channel/SetIntervals."""
        return await self._call(self.PATH_SET_INTERVALS, req, models.UpdateResult)

__all__ = ['ChannelService']
