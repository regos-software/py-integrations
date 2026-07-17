"""REGOS API service for SysConfig."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class SysConfigService(RegosAPIService):
    PATH_GET = "SysConfig/Get"
    PATH_EDIT = "SysConfig/Edit"
    REQUEST_MODELS = {
        'get': models.SysConfigGet,
    }

    async def get(self, req: models.SysConfigGet | dict[str, Any]) -> models.SysConfigArrayRegosObjectResult:
        """POST SysConfig/Get."""
        return await self._call(self.PATH_GET, req, models.SysConfigArrayRegosObjectResult)

    async def edit(self, req: list[models.SysConfigEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST SysConfig/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

__all__ = ['SysConfigService']
