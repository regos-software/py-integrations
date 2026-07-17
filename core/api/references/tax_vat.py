"""REGOS API service for TaxVat."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class TaxVatService(RegosAPIService):
    PATH_GET = "TaxVat/Get"
    PATH_ADD = "TaxVat/Add"
    PATH_EDIT = "TaxVat/Edit"
    PATH_DELETE = "TaxVat/Delete"
    REQUEST_MODELS = {
        'add': models.TaxVatAdd,
        'delete': models.TaxVatDelete,
        'edit': models.TaxVatEdit,
        'get': models.TaxVatGet,
    }

    async def get(self, req: models.TaxVatGet | dict[str, Any]) -> models.TaxVatRegosArrayResult:
        """POST TaxVat/Get."""
        return await self._call(self.PATH_GET, req, models.TaxVatRegosArrayResult)

    async def add(self, req: models.TaxVatAdd | dict[str, Any]) -> models.InsertResult:
        """POST TaxVat/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.TaxVatEdit | dict[str, Any]) -> models.UpdateResult:
        """POST TaxVat/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.TaxVatDelete | dict[str, Any]) -> models.UpdateResult:
        """POST TaxVat/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['TaxVatService']
