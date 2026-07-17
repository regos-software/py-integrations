"""REGOS API service for Session."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class SessionService(RegosAPIService):
    PATH_GET = "Session/Get"
    REQUEST_MODELS = {
        'get': models.SessionGet,
    }

    async def get(self, req: models.SessionGet | dict[str, Any]) -> models.SessionRegosArrayResult:
        """POST Session/Get."""
        return await self._call(self.PATH_GET, req, models.SessionRegosArrayResult)

__all__ = ['SessionService']
