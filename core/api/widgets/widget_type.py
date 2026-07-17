"""REGOS API service for WidgetType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class WidgetTypeService(RegosAPIService):
    PATH_GET = "WidgetType/Get"

    async def get(self, body: dict[str, Any] | None = None) -> models.WidgetTypeRegosArrayResult:
        """POST WidgetType/Get."""
        return await self._call(self.PATH_GET, body or {}, models.WidgetTypeRegosArrayResult)

__all__ = ['WidgetTypeService']
