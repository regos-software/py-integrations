"""REGOS API service for WorkAttendance."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class WorkAttendanceService(RegosAPIService):
    PATH_STATUS = "WorkAttendance/Status"
    PATH_CHECK_IN = "WorkAttendance/CheckIn"
    PATH_CHECK_OUT = "WorkAttendance/CheckOut"
    PATH_BREAK_START = "WorkAttendance/BreakStart"
    PATH_BREAK_END = "WorkAttendance/BreakEnd"
    PATH_CURRENT_SESSION = "WorkAttendance/CurrentSession"
    REQUEST_MODELS = {
        'break_end': models.WorkAttendanceBreakEnd,
        'break_start': models.WorkAttendanceBreakStart,
        'check_in': models.WorkAttendanceCheckIn,
        'check_out': models.WorkAttendanceCheckOut,
        'current_session': models.WorkAttendanceCurrentSession,
        'status': models.WorkAttendanceStatus,
    }

    async def status(self, req: models.WorkAttendanceStatus | dict[str, Any]) -> models.WorkUserAvailabilityRegosObjectResult:
        """POST WorkAttendance/Status."""
        return await self._call(self.PATH_STATUS, req, models.WorkUserAvailabilityRegosObjectResult)

    async def check_in(self, req: models.WorkAttendanceCheckIn | dict[str, Any]) -> models.InsertResult:
        """POST WorkAttendance/CheckIn."""
        return await self._call(self.PATH_CHECK_IN, req, models.InsertResult)

    async def check_out(self, req: models.WorkAttendanceCheckOut | dict[str, Any]) -> models.UpdateResult:
        """POST WorkAttendance/CheckOut."""
        return await self._call(self.PATH_CHECK_OUT, req, models.UpdateResult)

    async def break_start(self, req: models.WorkAttendanceBreakStart | dict[str, Any]) -> models.InsertResult:
        """POST WorkAttendance/BreakStart."""
        return await self._call(self.PATH_BREAK_START, req, models.InsertResult)

    async def break_end(self, req: models.WorkAttendanceBreakEnd | dict[str, Any]) -> models.UpdateResult:
        """POST WorkAttendance/BreakEnd."""
        return await self._call(self.PATH_BREAK_END, req, models.UpdateResult)

    async def current_session(self, req: models.WorkAttendanceCurrentSession | dict[str, Any]) -> models.WorkSessionRegosObjectResult:
        """POST WorkAttendance/CurrentSession."""
        return await self._call(self.PATH_CURRENT_SESSION, req, models.WorkSessionRegosObjectResult)

__all__ = ['WorkAttendanceService']
