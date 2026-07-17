"""REGOS API service for RetailOperationList."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RetailOperationListService(RegosAPIService):
    PATH_GET = "RetailOperationList/Get"
    REQUEST_MODELS = {
        'get': models.RetailOperationListGet,
    }

    async def get(self, req: models.RetailOperationListGet | dict[str, Any]) -> models.RetailOperationListRegosOffsettedArrayResult:
        """POST RetailOperationList/Get."""
        return await self._call(self.PATH_GET, req, models.RetailOperationListRegosOffsettedArrayResult)

__all__ = ['RetailOperationListService']
