"""REGOS API service for Language."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class LanguageService(RegosAPIService):
    PATH_GET = "Language/Get"

    async def get(self, body: dict[str, Any] | None = None) -> models.LanguageRegosArrayResult:
        """POST Language/Get."""
        return await self._call(self.PATH_GET, body or {}, models.LanguageRegosArrayResult)

__all__ = ['LanguageService']
