"""REGOS API service for TargetType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class TargetTypeService(RegosAPIService):
    PATH_GET = "TargetType/Get"

    async def get(self, body: dict[str, Any] | None = None) -> models.TargetTypeRegosArrayResult:
        """POST TargetType/Get."""
        return await self._call(self.PATH_GET, body or {}, models.TargetTypeRegosArrayResult)

__all__ = ['TargetTypeService']
