"""REGOS API service for TechMapOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class TechMapOperationService(RegosAPIService):
    PATH_GET = "TechMapOperation/Get"
    PATH_ADD = "TechMapOperation/Add"
    PATH_EDIT = "TechMapOperation/Edit"
    PATH_DELETE = "TechMapOperation/Delete"
    PATH_MOVE_OPERATIONS = "TechMapOperation/MoveOperations"
    REQUEST_MODELS = {
        'add': models.TechMapOperationAdd,
        'get': models.TechMapOperationGet,
        'move_operations': models.DocsOperationsMovement,
    }

    async def get(self, req: models.TechMapOperationGet | dict[str, Any]) -> models.TechMapOperationRegosOffsettedArrayResult:
        """POST TechMapOperation/Get."""
        return await self._call(self.PATH_GET, req, models.TechMapOperationRegosOffsettedArrayResult)

    async def add(self, req: models.TechMapOperationAdd | dict[str, Any]) -> models.UpdateResult:
        """POST TechMapOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.TechMapOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST TechMapOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.TechMapOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST TechMapOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST TechMapOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

__all__ = ['TechMapOperationService']
