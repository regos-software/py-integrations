"""REGOS API service for IntegrationGroup."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class IntegrationGroupService(RegosAPIService):
    PATH_GET = "IntegrationGroup/Get"
    REQUEST_MODELS = {
        'get': models.IntegrationGroupGet,
    }

    async def get(self, req: models.IntegrationGroupGet | dict[str, Any]) -> models.IntegrationGroupRegosArrayResult:
        """POST IntegrationGroup/Get."""
        return await self._call(self.PATH_GET, req, models.IntegrationGroupRegosArrayResult)

__all__ = ['IntegrationGroupService']
