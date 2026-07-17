"""REGOS API service for InOutOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class InOutOperationService(RegosAPIService):
    PATH_GET = "InOutOperation/Get"
    PATH_ADD = "InOutOperation/Add"
    PATH_EDIT = "InOutOperation/Edit"
    PATH_DELETE = "InOutOperation/Delete"
    PATH_MOVE_OPERATIONS = "InOutOperation/MoveOperations"
    PATH_COPY_OPERATIONS_FROM_DOC_INVENTORY = "InOutOperation/CopyOperationsFromDocInventory"
    REQUEST_MODELS = {
        'copy_operations_from_doc_inventory': models.DocsOperationsCopy,
        'get': models.InOutOperationGet,
        'move_operations': models.DocsOperationsMovement,
    }

    async def get(self, req: models.InOutOperationGet | dict[str, Any]) -> models.InOutOperationRegosOffsettedArrayResult:
        """POST InOutOperation/Get."""
        return await self._call(self.PATH_GET, req, models.InOutOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.InOutOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST InOutOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.InOutOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST InOutOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.InOutOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST InOutOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST InOutOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

    async def copy_operations_from_doc_inventory(self, req: models.DocsOperationsCopy | dict[str, Any]) -> models.UpdateResult:
        """POST InOutOperation/CopyOperationsFromDocInventory."""
        return await self._call(self.PATH_COPY_OPERATIONS_FROM_DOC_INVENTORY, req, models.UpdateResult)

__all__ = ['InOutOperationService']
