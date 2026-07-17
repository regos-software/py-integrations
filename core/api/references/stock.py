"""REGOS API service for Stock."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class StockService(RegosAPIService):
    PATH_GET = "Stock/Get"
    PATH_ADD = "Stock/Add"
    PATH_EDIT = "Stock/Edit"
    PATH_DELETE_MARK = "Stock/DeleteMark"
    PATH_DELETE = "Stock/Delete"
    PATH_DELETE_CONFIRM = "Stock/DeleteConfirm"
    REQUEST_MODELS = {
        'add': models.StockAdd,
        'delete': models.StockDelete,
        'delete_confirm': models.StockDeleteConfirm,
        'delete_mark': models.StockDeleteMark,
        'edit': models.StockEdit,
        'get': models.StockGet,
    }

    async def get(self, req: models.StockGet | dict[str, Any]) -> models.StockRegosOffsettedArrayResult:
        """POST Stock/Get."""
        return await self._call(self.PATH_GET, req, models.StockRegosOffsettedArrayResult)

    async def add(self, req: models.StockAdd | dict[str, Any]) -> models.InsertResult:
        """POST Stock/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.StockEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Stock/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete_mark(self, req: models.StockDeleteMark | dict[str, Any]) -> models.UpdateResult:
        """POST Stock/DeleteMark."""
        return await self._call(self.PATH_DELETE_MARK, req, models.UpdateResult)

    async def delete(self, req: models.StockDelete | dict[str, Any]) -> models.ApiResult:
        """POST Stock/Delete."""
        return await self._call(self.PATH_DELETE, req, models.ApiResult)

    async def delete_confirm(self, req: models.StockDeleteConfirm | dict[str, Any]) -> models.ApiResult:
        """POST Stock/DeleteConfirm."""
        return await self._call(self.PATH_DELETE_CONFIRM, req, models.ApiResult)

__all__ = ['StockService']
