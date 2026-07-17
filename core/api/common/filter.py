"""REGOS API service for Filter."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class FilterService(RegosAPIService):
    PATH_GET_FIELDS = "Filter/GetFields"
    REQUEST_MODELS = {
        'get_fields': models.FilterGetFields,
    }

    async def get_fields(self, req: models.FilterGetFields | dict[str, Any]) -> models.FilterFieldInfoRegosArrayResult:
        """POST Filter/GetFields."""
        return await self._call(self.PATH_GET_FIELDS, req, models.FilterFieldInfoRegosArrayResult)

__all__ = ['FilterService']
