"""REGOS API service for ReportPrepared."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ReportPreparedService(RegosAPIService):
    PATH_GET = "ReportPrepared/Get"
    PATH_SAVE = "ReportPrepared/Save"
    PATH_REMOVE = "ReportPrepared/Remove"
    REQUEST_MODELS = {
        'get': models.ReportPreparedGet,
        'remove': models.ReportPreparedRemove,
        'save': models.ReportPreparedSave,
    }

    async def get(self, req: models.ReportPreparedGet | dict[str, Any]) -> models.ReportPreparedArrayRegosObjectResult:
        """POST ReportPrepared/Get."""
        return await self._call(self.PATH_GET, req, models.ReportPreparedArrayRegosObjectResult)

    async def save(self, req: models.ReportPreparedSave | dict[str, Any]) -> models.UpdateResult:
        """POST ReportPrepared/Save."""
        return await self._call(self.PATH_SAVE, req, models.UpdateResult)

    async def remove(self, req: models.ReportPreparedRemove | dict[str, Any]) -> models.UpdateResult:
        """POST ReportPrepared/Remove."""
        return await self._call(self.PATH_REMOVE, req, models.UpdateResult)

__all__ = ['ReportPreparedService']
