"""REGOS API service for CustomerPersonalDocument."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class CustomerPersonalDocumentService(RegosAPIService):
    PATH_GET = "CustomerPersonalDocument/Get"
    PATH_ADD = "CustomerPersonalDocument/Add"
    PATH_EDIT = "CustomerPersonalDocument/Edit"
    PATH_REMOVE_FILE = "CustomerPersonalDocument/RemoveFile"
    PATH_DELETE = "CustomerPersonalDocument/Delete"
    REQUEST_MODELS = {
        'delete': models.CustomerPersonalDocumentDelete,
        'get': models.CustomerPersonalDocumentGet,
        'remove_file': models.CustomerPersonalDocumentRemoveFile,
    }

    async def get(self, req: models.CustomerPersonalDocumentGet | dict[str, Any]) -> models.CustomerPersonalDocumentRegosArrayResult:
        """POST CustomerPersonalDocument/Get."""
        return await self._call(self.PATH_GET, req, models.CustomerPersonalDocumentRegosArrayResult)

    async def add(self, body: dict[str, Any] | None = None) -> models.InsertResult:
        """POST CustomerPersonalDocument/Add."""
        return await self._call(self.PATH_ADD, body or {}, models.InsertResult)

    async def edit(self, body: dict[str, Any] | None = None) -> models.UpdateResult:
        """POST CustomerPersonalDocument/Edit."""
        return await self._call(self.PATH_EDIT, body or {}, models.UpdateResult)

    async def remove_file(self, req: models.CustomerPersonalDocumentRemoveFile | dict[str, Any]) -> models.UpdateResult:
        """POST CustomerPersonalDocument/RemoveFile."""
        return await self._call(self.PATH_REMOVE_FILE, req, models.UpdateResult)

    async def delete(self, req: models.CustomerPersonalDocumentDelete | dict[str, Any]) -> models.UpdateResult:
        """POST CustomerPersonalDocument/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['CustomerPersonalDocumentService']
