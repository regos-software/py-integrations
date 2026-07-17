"""REGOS API service for DocCheque."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocChequeService(RegosAPIService):
    PATH_GET = "DocCheque/Get"
    PATH_GET_SHORT = "DocCheque/GetShort"
    PATH_GET_FAVORITE_PERIOD = "DocCheque/GetFavoritePeriod"
    REQUEST_MODELS = {
        'get': models.DocChequeGet,
        'get_favorite_period': models.DocChequeGet,
        'get_short': models.DocChequeShortGet,
    }

    async def get(self, req: models.DocChequeGet | dict[str, Any]) -> models.DocChequeRegosOffsettedArrayResult:
        """POST DocCheque/Get."""
        return await self._call(self.PATH_GET, req, models.DocChequeRegosOffsettedArrayResult)

    async def get_short(self, req: models.DocChequeShortGet | dict[str, Any]) -> models.DocChequeShortRegosOffsettedArrayResult:
        """POST DocCheque/GetShort."""
        return await self._call(self.PATH_GET_SHORT, req, models.DocChequeShortRegosOffsettedArrayResult)

    async def get_favorite_period(self, req: models.DocChequeGet | dict[str, Any]) -> models.DocChequeRegosOffsettedArrayResult:
        """POST DocCheque/GetFavoritePeriod."""
        return await self._call(self.PATH_GET_FAVORITE_PERIOD, req, models.DocChequeRegosOffsettedArrayResult)

__all__ = ['DocChequeService']
