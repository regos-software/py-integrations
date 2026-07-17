"""REGOS API service for Translation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class TranslationService(RegosAPIService):
    PATH_GET = "Translation/Get"
    PATH_GET_TRANSLATION_PACKET = "Translation/GetTranslationPacket"
    REQUEST_MODELS = {
        'get': models.TranslationGet,
        'get_translation_packet': models.TranslationGet,
    }

    async def get(self, req: models.TranslationGet | dict[str, Any]) -> models.TranslationArrayRegosObjectResult:
        """POST Translation/Get."""
        return await self._call(self.PATH_GET, req, models.TranslationArrayRegosObjectResult)

    async def get_translation_packet(self, req: models.TranslationGet | dict[str, Any]) -> models.LanguageTranslationDataRegosObjectResult:
        """POST Translation/GetTranslationPacket."""
        return await self._call(self.PATH_GET_TRANSLATION_PACKET, req, models.LanguageTranslationDataRegosObjectResult)

__all__ = ['TranslationService']
