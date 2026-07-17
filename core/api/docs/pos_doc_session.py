"""REGOS API service for PosDocSession."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PosDocSessionService(RegosAPIService):
    PATH_GET = "pos/DocSession/get"
    PATH_GET_CURRENT = "pos/DocSession/getCurrent"
    PATH_OPEN = "pos/DocSession/open"
    PATH_CLOSE = "pos/DocSession/close"
    PATH_X_REPORT = "pos/DocSession/XReport"
    REQUEST_MODELS = {
        'close': models.PosDocSessionClose,
        'get': models.PosDocSessionGet,
    }

    async def get(self, req: models.PosDocSessionGet | dict[str, Any]) -> models.PosDocSessionArrayRegosObjectResult:
        """POST pos/DocSession/get."""
        return await self._call(self.PATH_GET, req, models.PosDocSessionArrayRegosObjectResult)

    async def get_current(self, body: dict[str, Any] | None = None) -> models.PosDocSessionRegosObjectResult:
        """POST pos/DocSession/getCurrent."""
        return await self._call(self.PATH_GET_CURRENT, body or {}, models.PosDocSessionRegosObjectResult)

    async def open(self, body: dict[str, Any] | None = None) -> models.Insert_uuid_Result:
        """POST pos/DocSession/open."""
        return await self._call(self.PATH_OPEN, body or {}, models.Insert_uuid_Result)

    async def close(self, req: models.PosDocSessionClose | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST pos/DocSession/close."""
        return await self._call(self.PATH_CLOSE, req, models.Insert_uuid_Result)

    async def x_report(self, body: dict[str, Any] | None = None) -> models.PosDocSessionReportRegosObjectResult:
        """POST pos/DocSession/XReport."""
        return await self._call(self.PATH_X_REPORT, body or {}, models.PosDocSessionReportRegosObjectResult)

__all__ = ['PosDocSessionService']
