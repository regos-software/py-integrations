"""REGOS API service for DocCashSession."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocCashSessionService(RegosAPIService):
    PATH_GET = "DocCashSession/Get"
    REQUEST_MODELS = {
        'get': models.DocCashSessionGet,
    }

    async def get(self, req: models.DocCashSessionGet | dict[str, Any]) -> models.DocCashSessionRegosOffsettedArrayResult:
        """POST DocCashSession/Get."""
        return await self._call(self.PATH_GET, req, models.DocCashSessionRegosOffsettedArrayResult)

__all__ = ['DocCashSessionService']
