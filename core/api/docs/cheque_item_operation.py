"""REGOS API service for ChequeItemOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ChequeItemOperationService(RegosAPIService):
    PATH_GET = "ChequeItemOperation/Get"
    REQUEST_MODELS = {
        'get': models.DocChequeOperationGet,
    }

    async def get(self, req: models.DocChequeOperationGet | dict[str, Any]) -> models.DocChequeOperationRegosArrayResult:
        """POST ChequeItemOperation/Get."""
        return await self._call(self.PATH_GET, req, models.DocChequeOperationRegosArrayResult)

__all__ = ['ChequeItemOperationService']
