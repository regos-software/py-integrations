"""REGOS API service for Sys."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class SysService(RegosAPIService):
    PATH_GET_INFO = "Sys/GetInfo"

    async def get_info(self, body: dict[str, Any] | None = None) -> models.ApiResult:
        """POST Sys/GetInfo."""
        return await self._call(self.PATH_GET_INFO, body or {}, models.ApiResult)

__all__ = ['SysService']
