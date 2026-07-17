"""REGOS API service for DocAdditionalExpensesOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocAdditionalExpensesOperationService(RegosAPIService):
    PATH_GET = "DocAdditionalExpensesOperation/Get"
    PATH_ADD = "DocAdditionalExpensesOperation/Add"
    PATH_EDIT = "DocAdditionalExpensesOperation/Edit"
    PATH_DELETE = "DocAdditionalExpensesOperation/Delete"
    REQUEST_MODELS = {
        'get': models.DocAdditionalExpensesOperationGet,
    }

    async def get(self, req: models.DocAdditionalExpensesOperationGet | dict[str, Any]) -> models.DocAdditionalExpensesOperationRegosOffsettedArrayResult:
        """POST DocAdditionalExpensesOperation/Get."""
        return await self._call(self.PATH_GET, req, models.DocAdditionalExpensesOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.DocAdditionalExpensesOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST DocAdditionalExpensesOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.DocAdditionalExpensesOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST DocAdditionalExpensesOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.Base_ID] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST DocAdditionalExpensesOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DocAdditionalExpensesOperationService']
