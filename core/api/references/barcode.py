"""REGOS API service for Barcode."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class BarcodeService(RegosAPIService):
    PATH_GET = "Barcode/Get"
    PATH_ADD = "Barcode/Add"
    PATH_ADD_EAN13 = "Barcode/AddEAN13"
    PATH_SET_BASE = "Barcode/SetBase"
    PATH_DELETE = "Barcode/Delete"
    PATH_GENERATE_EAN13 = "Barcode/GenerateEan13"
    PATH_FILL_EMPTY_BARCODE_ITEMS = "Barcode/FillEmptyBarcodeItems"
    REQUEST_MODELS = {
        'add': models.BarcodeAdd,
        'add_ean13': models.BarcodeAddEAN13,
        'delete': models.BarcodeDelete,
        'get': models.BarcodeGet,
        'set_base': models.Barcode_SetBase,
    }

    async def get(self, req: models.BarcodeGet | dict[str, Any]) -> models.BarcodeArrayRegosObjectResult:
        """POST Barcode/Get."""
        return await self._call(self.PATH_GET, req, models.BarcodeArrayRegosObjectResult)

    async def add(self, req: models.BarcodeAdd | dict[str, Any]) -> models.InsertResult:
        """POST Barcode/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def add_ean13(self, req: models.BarcodeAddEAN13 | dict[str, Any]) -> models.InsertResult:
        """POST Barcode/AddEAN13."""
        return await self._call(self.PATH_ADD_EAN13, req, models.InsertResult)

    async def set_base(self, req: models.Barcode_SetBase | dict[str, Any]) -> models.UpdateResult:
        """POST Barcode/SetBase."""
        return await self._call(self.PATH_SET_BASE, req, models.UpdateResult)

    async def delete(self, req: models.BarcodeDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Barcode/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def generate_ean13(self, body: dict[str, Any] | None = None) -> models.EAN13RegosObjectResult:
        """POST Barcode/GenerateEan13."""
        return await self._call(self.PATH_GENERATE_EAN13, body or {}, models.EAN13RegosObjectResult)

    async def fill_empty_barcode_items(self, body: dict[str, Any] | None = None) -> models.UpdateResult:
        """POST Barcode/FillEmptyBarcodeItems."""
        return await self._call(self.PATH_FILL_EMPTY_BARCODE_ITEMS, body or {}, models.UpdateResult)

__all__ = ['BarcodeService']
