"""REGOS API service for WidgetData."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class WidgetDataService(RegosAPIService):
    PATH_GET = "WidgetData/Get"
    REQUEST_MODELS = {
        'get': models.Base_ID,
    }

    async def get(self, req: models.Base_ID | dict[str, Any]) -> models.ObjectRegosArrayResult:
        """POST WidgetData/Get."""
        return await self._call(self.PATH_GET, req, models.ObjectRegosArrayResult)

__all__ = ['WidgetDataService']
