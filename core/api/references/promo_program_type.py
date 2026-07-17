"""REGOS API service for PromoProgramType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PromoProgramTypeService(RegosAPIService):
    PATH_GET = "PromoProgramType/Get"
    REQUEST_MODELS = {
        'get': models.PromoProgramTypeGet,
    }

    async def get(self, req: models.PromoProgramTypeGet | dict[str, Any]) -> models.PromoProgramTypeRegosArrayResult:
        """POST PromoProgramType/Get."""
        return await self._call(self.PATH_GET, req, models.PromoProgramTypeRegosArrayResult)

__all__ = ['PromoProgramTypeService']
