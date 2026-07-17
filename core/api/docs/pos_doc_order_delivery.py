"""REGOS API service for PosDocOrderDelivery."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PosDocOrderDeliveryService(RegosAPIService):
    PATH_GET = "pos/DocOrderDelivery/get"
    REQUEST_MODELS = {
        'get': models.DocOrderDeliveryGet,
    }

    async def get(self, req: models.DocOrderDeliveryGet | dict[str, Any]) -> models.DocOrderDeliveryRegosOffsettedArrayResult:
        """POST pos/DocOrderDelivery/get."""
        return await self._call(self.PATH_GET, req, models.DocOrderDeliveryRegosOffsettedArrayResult)

__all__ = ['PosDocOrderDeliveryService']
