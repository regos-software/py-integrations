"""REGOS API service for DocumentStatus."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocumentStatusService(RegosAPIService):
    PATH_GET = "DocumentStatus/get"
    REQUEST_MODELS = {
        'get': models.DocumentStatusGet,
    }

    async def get(self, req: models.DocumentStatusGet | dict[str, Any]) -> models.DocumentStatusRegosArrayResult:
        """POST DocumentStatus/get."""
        return await self._call(self.PATH_GET, req, models.DocumentStatusRegosArrayResult)

__all__ = ['DocumentStatusService']
