"""REGOS API service for DocContractFile."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocContractFileService(RegosAPIService):
    PATH_GET = "DocContractFile/Get"
    PATH_ADD = "DocContractFile/Add"
    PATH_DELETE = "DocContractFile/Delete"
    REQUEST_MODELS = {
        'delete': models.DocContractFileDelete,
        'get': models.DocContractFileGet,
    }

    async def get(self, req: models.DocContractFileGet | dict[str, Any]) -> models.DocContractFileRegosArrayResult:
        """POST DocContractFile/Get."""
        return await self._call(self.PATH_GET, req, models.DocContractFileRegosArrayResult)

    async def add(self, body: dict[str, Any] | None = None) -> models.InsertResult:
        """POST DocContractFile/Add."""
        return await self._call(self.PATH_ADD, body or {}, models.InsertResult)

    async def delete(self, req: models.DocContractFileDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocContractFile/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DocContractFileService']
