"""REGOS API service for EditedExchangeRateLog."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class EditedExchangeRateLogService(RegosAPIService):
    PATH_GET = "EditedExchangeRateLog/Get"
    REQUEST_MODELS = {
        'get': models.EditedExchangeRateLogGet,
    }

    async def get(self, req: models.EditedExchangeRateLogGet | dict[str, Any]) -> models.EditedExchangeRateLogRegosOffsettedArrayResult:
        """POST EditedExchangeRateLog/Get."""
        return await self._call(self.PATH_GET, req, models.EditedExchangeRateLogRegosOffsettedArrayResult)

__all__ = ['EditedExchangeRateLogService']
