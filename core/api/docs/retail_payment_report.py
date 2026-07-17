"""REGOS API service for RetailPaymentReport."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RetailPaymentReportService(RegosAPIService):
    PATH_GET = "RetailPaymentReport/Get"
    REQUEST_MODELS = {
        'get': models.RetailPaymentReportGet,
    }

    async def get(self, req: models.RetailPaymentReportGet | dict[str, Any]) -> models.RetailPaymentReportRegosArrayResult:
        """POST RetailPaymentReport/Get."""
        return await self._call(self.PATH_GET, req, models.RetailPaymentReportRegosArrayResult)

__all__ = ['RetailPaymentReportService']
