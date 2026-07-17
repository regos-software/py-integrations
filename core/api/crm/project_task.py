"""REGOS API service for ProjectTask."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ProjectTaskService(RegosAPIService):
    PATH_GET = "ProjectTask/Get"
    PATH_ADD = "ProjectTask/Add"
    PATH_EDIT = "ProjectTask/Edit"
    PATH_DELETE = "ProjectTask/Delete"
    PATH_SET_STATUS = "ProjectTask/SetStatus"
    PATH_SET_DUE = "ProjectTask/SetDue"
    PATH_SET_PROJECT = "ProjectTask/SetProject"
    PATH_SET_RESPONSIBLE = "ProjectTask/SetResponsible"
    PATH_SET_OBSERVERS = "ProjectTask/SetObservers"
    REQUEST_MODELS = {
        'add': models.ProjectTaskAdd,
        'delete': models.ProjectTaskDelete,
        'edit': models.ProjectTaskEdit,
        'get': models.ProjectTaskGet,
        'set_due': models.ProjectTaskSetDue,
        'set_observers': models.ProjectTaskSetObservers,
        'set_project': models.ProjectTaskSetProject,
        'set_responsible': models.ProjectTaskSetResponsible,
        'set_status': models.ProjectTaskSetStatus,
    }

    async def get(self, req: models.ProjectTaskGet | dict[str, Any]) -> models.ProjectTaskRegosOffsettedArrayResult:
        """POST ProjectTask/Get."""
        return await self._call(self.PATH_GET, req, models.ProjectTaskRegosOffsettedArrayResult)

    async def add(self, req: models.ProjectTaskAdd | dict[str, Any]) -> models.InsertResult:
        """POST ProjectTask/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.ProjectTaskEdit | dict[str, Any]) -> models.UpdateResult:
        """POST ProjectTask/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.ProjectTaskDelete | dict[str, Any]) -> models.UpdateResult:
        """POST ProjectTask/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_status(self, req: models.ProjectTaskSetStatus | dict[str, Any]) -> models.UpdateResult:
        """POST ProjectTask/SetStatus."""
        return await self._call(self.PATH_SET_STATUS, req, models.UpdateResult)

    async def set_due(self, req: models.ProjectTaskSetDue | dict[str, Any]) -> models.UpdateResult:
        """POST ProjectTask/SetDue."""
        return await self._call(self.PATH_SET_DUE, req, models.UpdateResult)

    async def set_project(self, req: models.ProjectTaskSetProject | dict[str, Any]) -> models.UpdateResult:
        """POST ProjectTask/SetProject."""
        return await self._call(self.PATH_SET_PROJECT, req, models.UpdateResult)

    async def set_responsible(self, req: models.ProjectTaskSetResponsible | dict[str, Any]) -> models.UpdateResult:
        """POST ProjectTask/SetResponsible."""
        return await self._call(self.PATH_SET_RESPONSIBLE, req, models.UpdateResult)

    async def set_observers(self, req: models.ProjectTaskSetObservers | dict[str, Any]) -> models.UpdateResult:
        """POST ProjectTask/SetObservers."""
        return await self._call(self.PATH_SET_OBSERVERS, req, models.UpdateResult)

__all__ = ['ProjectTaskService']
