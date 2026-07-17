"""REGOS API service for SizeChart."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class SizeChartService(RegosAPIService):
    PATH_GET = "SizeChart/Get"
    PATH_ADD = "SizeChart/Add"
    PATH_EDIT = "SizeChart/Edit"
    PATH_DELETE = "SizeChart/Delete"
    REQUEST_MODELS = {
        'add': models.SizeChartAdd,
        'delete': models.SizeChartDelete,
        'edit': models.SizeChartEdit,
        'get': models.SizeChartGet,
    }

    async def get(self, req: models.SizeChartGet | dict[str, Any]) -> models.SizeChartRegosOffsettedArrayResult:
        """POST SizeChart/Get."""
        return await self._call(self.PATH_GET, req, models.SizeChartRegosOffsettedArrayResult)

    async def add(self, req: models.SizeChartAdd | dict[str, Any]) -> models.InsertResult:
        """POST SizeChart/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.SizeChartEdit | dict[str, Any]) -> models.UpdateResult:
        """POST SizeChart/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.SizeChartDelete | dict[str, Any]) -> models.UpdateResult:
        """POST SizeChart/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['SizeChartService']
