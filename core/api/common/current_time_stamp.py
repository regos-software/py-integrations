"""REGOS API service for CurrentTimeStamp."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class CurrentTimeStampService(RegosAPIService):
    PATH_GET = "CurrentTimeStamp/Get"

    async def get(self, body: dict[str, Any] | None = None) -> models.Int64RegosObjectResult:
        """POST CurrentTimeStamp/Get."""
        return await self._call(self.PATH_GET, body or {}, models.Int64RegosObjectResult)

__all__ = ['CurrentTimeStampService']
