"""REGOS API service for Project."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ProjectService(RegosAPIService):
    PATH_GET = "Project/Get"
    PATH_ADD = "Project/Add"
    PATH_EDIT = "Project/Edit"
    PATH_DELETE = "Project/Delete"
    PATH_SET_ACCESS = "Project/SetAccess"
    PATH_SET_RESPONSIBLE = "Project/SetResponsible"
    REQUEST_MODELS = {
        'add': models.ProjectAdd,
        'delete': models.ProjectDelete,
        'edit': models.ProjectEdit,
        'get': models.ProjectGet,
        'set_access': models.ProjectSetAccess,
        'set_responsible': models.ProjectSetResponsible,
    }

    async def get(self, req: models.ProjectGet | dict[str, Any]) -> models.ProjectRegosOffsettedArrayResult:
        """POST Project/Get."""
        return await self._call(self.PATH_GET, req, models.ProjectRegosOffsettedArrayResult)

    async def add(self, req: models.ProjectAdd | dict[str, Any]) -> models.InsertResult:
        """POST Project/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.ProjectEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Project/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.ProjectDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Project/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_access(self, req: models.ProjectSetAccess | dict[str, Any]) -> models.UpdateResult:
        """POST Project/SetAccess."""
        return await self._call(self.PATH_SET_ACCESS, req, models.UpdateResult)

    async def set_responsible(self, req: models.ProjectSetResponsible | dict[str, Any]) -> models.UpdateResult:
        """POST Project/SetResponsible."""
        return await self._call(self.PATH_SET_RESPONSIBLE, req, models.UpdateResult)

__all__ = ['ProjectService']
