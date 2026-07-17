"""REGOS API service for Storage."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class StorageService(RegosAPIService):
    PATH_GET = "Storage/Get"
    PATH_CLEANUP = "Storage/Cleanup"
    REQUEST_MODELS = {
        'cleanup': models.StorageCleanup,
        'get': models.StorageGet,
    }

    async def get(self, req: models.StorageGet | dict[str, Any]) -> models.StorageRegosObjectResult:
        """POST Storage/Get."""
        return await self._call(self.PATH_GET, req, models.StorageRegosObjectResult)

    async def cleanup(self, req: models.StorageCleanup | dict[str, Any]) -> models.BooleanRegosObjectResult:
        """POST Storage/Cleanup."""
        return await self._call(self.PATH_CLEANUP, req, models.BooleanRegosObjectResult)

__all__ = ['StorageService']
