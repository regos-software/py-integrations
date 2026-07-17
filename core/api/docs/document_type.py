"""REGOS API service for DocumentType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocumentTypeService(RegosAPIService):
    PATH_GET = "DocumentType/Get"
    REQUEST_MODELS = {
        'get': models.DocumentTypeGet,
    }

    async def get(self, req: models.DocumentTypeGet | dict[str, Any]) -> models.DocumentTypeArrayRegosObjectResult:
        """POST DocumentType/Get."""
        return await self._call(self.PATH_GET, req, models.DocumentTypeArrayRegosObjectResult)

__all__ = ['DocumentTypeService']
