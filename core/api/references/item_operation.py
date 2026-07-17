"""REGOS API service for ItemOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ItemOperationService(RegosAPIService):
    PATH_GET = "ItemOperation/Get"
    REQUEST_MODELS = {
        'get': models.ItemOperationGet,
    }

    async def get(self, req: models.ItemOperationGet | dict[str, Any]) -> models.ItemOperationRegosOffsettedArrayResult:
        """POST ItemOperation/Get."""
        return await self._call(self.PATH_GET, req, models.ItemOperationRegosOffsettedArrayResult)

__all__ = ['ItemOperationService']
