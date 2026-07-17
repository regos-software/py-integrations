"""REGOS API service for WorkSchedule."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class WorkScheduleService(RegosAPIService):
    PATH_GET = "WorkSchedule/Get"
    PATH_GET_INTERVALS = "WorkSchedule/GetIntervals"
    PATH_GET_EXCEPTIONS = "WorkSchedule/GetExceptions"
    PATH_ADD = "WorkSchedule/Add"
    PATH_EDIT = "WorkSchedule/Edit"
    PATH_DELETE = "WorkSchedule/Delete"
    PATH_SET_DEFAULT = "WorkSchedule/SetDefault"
    PATH_SET_INTERVALS = "WorkSchedule/SetIntervals"
    PATH_SET_EXCEPTIONS = "WorkSchedule/SetExceptions"
    REQUEST_MODELS = {
        'add': models.WorkScheduleAdd,
        'delete': models.WorkScheduleDelete,
        'edit': models.WorkScheduleEdit,
        'get': models.WorkScheduleGet,
        'get_exceptions': models.WorkScheduleGetExceptions,
        'get_intervals': models.WorkScheduleGetIntervals,
        'set_default': models.WorkScheduleSetDefault,
        'set_exceptions': models.WorkScheduleSetExceptions,
        'set_intervals': models.WorkScheduleSetIntervals,
    }

    async def get(self, req: models.WorkScheduleGet | dict[str, Any]) -> models.WorkScheduleRegosOffsettedArrayResult:
        """POST WorkSchedule/Get."""
        return await self._call(self.PATH_GET, req, models.WorkScheduleRegosOffsettedArrayResult)

    async def get_intervals(self, req: models.WorkScheduleGetIntervals | dict[str, Any]) -> models.WorkScheduleIntervalRegosArrayResult:
        """POST WorkSchedule/GetIntervals."""
        return await self._call(self.PATH_GET_INTERVALS, req, models.WorkScheduleIntervalRegosArrayResult)

    async def get_exceptions(self, req: models.WorkScheduleGetExceptions | dict[str, Any]) -> models.WorkScheduleExceptionRegosArrayResult:
        """POST WorkSchedule/GetExceptions."""
        return await self._call(self.PATH_GET_EXCEPTIONS, req, models.WorkScheduleExceptionRegosArrayResult)

    async def add(self, req: models.WorkScheduleAdd | dict[str, Any]) -> models.InsertResult:
        """POST WorkSchedule/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.WorkScheduleEdit | dict[str, Any]) -> models.UpdateResult:
        """POST WorkSchedule/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.WorkScheduleDelete | dict[str, Any]) -> models.UpdateResult:
        """POST WorkSchedule/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_default(self, req: models.WorkScheduleSetDefault | dict[str, Any]) -> models.UpdateResult:
        """POST WorkSchedule/SetDefault."""
        return await self._call(self.PATH_SET_DEFAULT, req, models.UpdateResult)

    async def set_intervals(self, req: models.WorkScheduleSetIntervals | dict[str, Any]) -> models.UpdateResult:
        """POST WorkSchedule/SetIntervals."""
        return await self._call(self.PATH_SET_INTERVALS, req, models.UpdateResult)

    async def set_exceptions(self, req: models.WorkScheduleSetExceptions | dict[str, Any]) -> models.UpdateResult:
        """POST WorkSchedule/SetExceptions."""
        return await self._call(self.PATH_SET_EXCEPTIONS, req, models.UpdateResult)

__all__ = ['WorkScheduleService']
