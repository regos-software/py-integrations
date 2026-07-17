"""REGOS API service for Pipeline."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PipelineService(RegosAPIService):
    PATH_GET = "Pipeline/Get"
    PATH_ADD = "Pipeline/Add"
    PATH_EDIT = "Pipeline/Edit"
    PATH_SET_ACCESS = "Pipeline/SetAccess"
    PATH_DELETE = "Pipeline/Delete"
    PATH_SET_STAGES = "Pipeline/SetStages"
    REQUEST_MODELS = {
        'add': models.PipelineAdd,
        'delete': models.PipelineDelete,
        'edit': models.PipelineEdit,
        'get': models.PipelineGet,
        'set_access': models.PipelineSetAccess,
        'set_stages': models.PipelineSetStages,
    }

    async def get(self, req: models.PipelineGet | dict[str, Any]) -> models.PipelineRegosOffsettedArrayResult:
        """POST Pipeline/Get."""
        return await self._call(self.PATH_GET, req, models.PipelineRegosOffsettedArrayResult)

    async def add(self, req: models.PipelineAdd | dict[str, Any]) -> models.InsertResult:
        """POST Pipeline/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.PipelineEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Pipeline/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def set_access(self, req: models.PipelineSetAccess | dict[str, Any]) -> models.UpdateResult:
        """POST Pipeline/SetAccess."""
        return await self._call(self.PATH_SET_ACCESS, req, models.UpdateResult)

    async def delete(self, req: models.PipelineDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Pipeline/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_stages(self, req: models.PipelineSetStages | dict[str, Any]) -> models.UpdateResult:
        """POST Pipeline/SetStages."""
        return await self._call(self.PATH_SET_STAGES, req, models.UpdateResult)

__all__ = ['PipelineService']
