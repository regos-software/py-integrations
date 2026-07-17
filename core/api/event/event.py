"""REGOS API service for Event."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class EventService(RegosAPIService):
    PATH_GET = "Event/Get"
    REQUEST_MODELS = {
        'get': models.EventGet,
    }

    async def get(self, req: models.EventGet | dict[str, Any]) -> models.EventGetResultRegosObjectResult:
        """POST Event/Get."""
        return await self._call(self.PATH_GET, req, models.EventGetResultRegosObjectResult)

__all__ = ['EventService']
