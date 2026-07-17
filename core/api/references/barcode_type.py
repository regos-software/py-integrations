"""REGOS API service for BarcodeType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class BarcodeTypeService(RegosAPIService):
    PATH_GET = "BarcodeType/Get"

    async def get(self, body: dict[str, Any] | None = None) -> models.BarcodeTypeRegosArrayResult:
        """POST BarcodeType/Get."""
        return await self._call(self.PATH_GET, body or {}, models.BarcodeTypeRegosArrayResult)

__all__ = ['BarcodeTypeService']
