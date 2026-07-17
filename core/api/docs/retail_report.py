"""REGOS API service for RetailReport."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RetailReportService(RegosAPIService):
    PATH_COUNTS = "RetailReport/Counts"
    PATH_PAYMENTS = "RetailReport/Payments"
    PATH_OPERATIONS = "RetailReport/Operations"
    REQUEST_MODELS = {
        'counts': models.RetailReportCountGet,
        'operations': models.RetailReportOperationGet,
        'payments': models.RetailReportPaymentGet,
    }

    async def counts(self, req: models.RetailReportCountGet | dict[str, Any]) -> models.RetailReportCountRegosArrayResult:
        """POST RetailReport/Counts."""
        return await self._call(self.PATH_COUNTS, req, models.RetailReportCountRegosArrayResult)

    async def payments(self, req: models.RetailReportPaymentGet | dict[str, Any]) -> models.RetailReportPaymentRegosArrayResult:
        """POST RetailReport/Payments."""
        return await self._call(self.PATH_PAYMENTS, req, models.RetailReportPaymentRegosArrayResult)

    async def operations(self, req: models.RetailReportOperationGet | dict[str, Any]) -> models.RetailReportOperationRegosOffsettedArrayResult:
        """POST RetailReport/Operations."""
        return await self._call(self.PATH_OPERATIONS, req, models.RetailReportOperationRegosOffsettedArrayResult)

__all__ = ['RetailReportService']
