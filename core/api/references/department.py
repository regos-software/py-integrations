"""REGOS API service for Department."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DepartmentService(RegosAPIService):
    PATH_GET = "Department/Get"
    PATH_ADD = "Department/Add"
    PATH_EDIT = "Department/Edit"
    PATH_DELETE = "Department/Delete"
    REQUEST_MODELS = {
        'add': models.DepartmentAdd,
        'delete': models.DepartmentDelete,
        'edit': models.DepartmentEdit,
        'get': models.DepartmentGet,
    }

    async def get(self, req: models.DepartmentGet | dict[str, Any]) -> models.DepartmentRegosOffsettedArrayResult:
        """POST Department/Get."""
        return await self._call(self.PATH_GET, req, models.DepartmentRegosOffsettedArrayResult)

    async def add(self, req: models.DepartmentAdd | dict[str, Any]) -> models.InsertResult:
        """POST Department/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.DepartmentEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Department/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.DepartmentDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Department/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['DepartmentService']
