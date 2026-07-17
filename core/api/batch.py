"""REGOS API service for Batch."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class BatchService(RegosAPIService):
    PATH_BATCH = "batch"
    REQUEST_MODELS = {
        'batch': models.BatchRequest,
    }

    async def batch(self, req: models.BatchRequest | dict[str, Any]) -> models.BatchResponseRegosObjectResult:
        """POST batch."""
        return await self._call(self.PATH_BATCH, req, models.BatchResponseRegosObjectResult)

    async def run(self, req: models.BatchRequest | dict[str, Any]) -> models.BatchResponseRegosObjectResult:
        """Backward-compatible alias used by existing integrations."""
        return await self.batch(req)

__all__ = ['BatchService']
