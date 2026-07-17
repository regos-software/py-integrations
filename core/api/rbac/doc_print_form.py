"""REGOS API service for DocPrintForm."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocPrintFormService(RegosAPIService):
    PATH_GET = "DocPrintForm/Get"
    PATH_PREPARE = "DocPrintForm/Prepare"
    PATH_ADD = "DocPrintForm/Add"
    PATH_EDIT = "DocPrintForm/Edit"
    PATH_DELETE = "DocPrintForm/Delete"
    REQUEST_MODELS = {
        'delete': models.DocPrintFormDelete,
        'get': models.DocPrintFormGet,
        'prepare': models.DocPrintFormPrepare,
    }

    async def get(self, req: models.DocPrintFormGet | dict[str, Any]) -> models.DocPrintFormRegosArrayResult:
        """POST DocPrintForm/Get."""
        return await self._call(self.PATH_GET, req, models.DocPrintFormRegosArrayResult)

    async def prepare(self, req: models.DocPrintFormPrepare | dict[str, Any]) -> models.DocPrintFormPreparedFileRegosObjectResult:
        """POST DocPrintForm/Prepare."""
        return await self._call(self.PATH_PREPARE, req, models.DocPrintFormPreparedFileRegosObjectResult)

    async def add(self, body: dict[str, Any] | None = None) -> models.InsertResult:
        """POST DocPrintForm/Add."""
        return await self._call(self.PATH_ADD, body or {}, models.InsertResult)

    async def edit(self, body: dict[str, Any] | None = None) -> models.UpdateResult:
        """POST DocPrintForm/Edit."""
        return await self._call(self.PATH_EDIT, body or {}, models.UpdateResult)

    async def delete(self, req: models.DocPrintFormDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocPrintForm/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DocPrintFormService']
