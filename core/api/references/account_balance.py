"""REGOS API service for AccountBalance."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class AccountBalanceService(RegosAPIService):
    PATH_GET = "AccountBalance/Get"
    REQUEST_MODELS = {
        'get': models.AccountGet,
    }

    async def get(self, req: models.AccountGet | dict[str, Any]) -> models.AccountBalanceRegosOffsettedArrayResult:
        """POST AccountBalance/Get."""
        return await self._call(self.PATH_GET, req, models.AccountBalanceRegosOffsettedArrayResult)

__all__ = ['AccountBalanceService']
