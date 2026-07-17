"""REGOS API service for DocPeriodClosing."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocPeriodClosingService(RegosAPIService):
    PATH_IS_CAN_DO = "DocPeriodClosing/IsCanDo"
    PATH_GET = "DocPeriodClosing/Get"
    PATH_ADD = "DocPeriodClosing/Add"
    PATH_EDIT = "DocPeriodClosing/Edit"
    PATH_DELETE = "DocPeriodClosing/Delete"
    PATH_CANCEL_CLOSE = "DocPeriodClosing/cancelClose"
    REQUEST_MODELS = {
        'add': models.DocPeriodClosingAdd,
        'cancel_close': models.DocPeriodClosingCancelClose,
        'delete': models.DocPeriodClosingDelete,
        'edit': models.DocPeriodClosingEdit,
        'get': models.DocPeriodClosingGet,
        'is_can_do': models.DocPeriodClosingCheckGet,
    }

    async def is_can_do(self, req: models.DocPeriodClosingCheckGet | dict[str, Any]) -> models.DocPeriodClosingCheckRegosOffsettedObjectResult:
        """POST DocPeriodClosing/IsCanDo."""
        return await self._call(self.PATH_IS_CAN_DO, req, models.DocPeriodClosingCheckRegosOffsettedObjectResult)

    async def get(self, req: models.DocPeriodClosingGet | dict[str, Any]) -> models.DocPeriodClosingRegosOffsettedArrayResult:
        """POST DocPeriodClosing/Get."""
        return await self._call(self.PATH_GET, req, models.DocPeriodClosingRegosOffsettedArrayResult)

    async def add(self, req: models.DocPeriodClosingAdd | dict[str, Any]) -> models.InsertResult:
        """POST DocPeriodClosing/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DocPeriodClosingEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocPeriodClosing/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.DocPeriodClosingDelete | dict[str, Any]) -> models.UpdateResult:
        """POST DocPeriodClosing/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def cancel_close(self, req: models.DocPeriodClosingCancelClose | dict[str, Any]) -> models.UpdateResult:
        """POST DocPeriodClosing/cancelClose."""
        return await self._call(self.PATH_CANCEL_CLOSE, req, models.UpdateResult)

__all__ = ['DocPeriodClosingService']
