"""REGOS API service for DocContract."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocContractService(RegosAPIService):
    PATH_GET = "DocContract/Get"
    PATH_GET_SHORT = "DocContract/GetShort"
    PATH_ADD = "DocContract/Add"
    PATH_EDIT = "DocContract/Edit"
    PATH_DELETE_MARK = "DocContract/DeleteMark"
    PATH_DELETE = "DocContract/Delete"
    REQUEST_MODELS = {
        'add': models.DocContractAdd,
        'delete': models.DocContractDelete,
        'delete_mark': models.DocContractDeleteMark,
        'edit': models.DocContractEdit,
        'get': models.DocContractGet,
        'get_short': models.DocContractGet,
    }

    async def get(self, req: models.DocContractGet | dict[str, Any]) -> models.DocContractRegosOffsettedArrayResult:
        """POST DocContract/Get."""
        return await self._call(self.PATH_GET, req, models.DocContractRegosOffsettedArrayResult)

    async def get_short(self, req: models.DocContractGet | dict[str, Any]) -> models.DocContractShortRegosOffsettedArrayResult:
        """POST DocContract/GetShort."""
        return await self._call(self.PATH_GET_SHORT, req, models.DocContractShortRegosOffsettedArrayResult)

    async def add(self, req: models.DocContractAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocContract/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocContractEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocContract/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.DocContractDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST DocContract/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.DocContractDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocContract/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DocContractService']
