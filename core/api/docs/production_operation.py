"""REGOS API service for ProductionOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ProductionOperationService(RegosAPIService):
    PATH_GET = "ProductionOperation/Get"
    PATH_ADD = "ProductionOperation/Add"
    PATH_EDIT = "ProductionOperation/Edit"
    PATH_REPLACE_OPR_TECH_MAP = "ProductionOperation/ReplaceOprTechMap"
    PATH_DELETE = "ProductionOperation/Delete"
    PATH_MOVE_OPERATIONS = "ProductionOperation/MoveOperations"
    REQUEST_MODELS = {
        'add': models.ProductionOperationAdd,
        'delete': models.ProductionOperationDelete,
        'get': models.ProductionOperationGet,
        'move_operations': models.DocsOperationsMovement,
        'replace_opr_tech_map': models.ProductionOperationReplaceOprTechMap,
    }

    async def get(self, req: models.ProductionOperationGet | dict[str, Any]) -> models.ProductionOperationRegosOffsettedArrayResult:
        """POST ProductionOperation/Get."""
        return await self._call(self.PATH_GET, req, models.ProductionOperationRegosOffsettedArrayResult)

    async def add(self, req: models.ProductionOperationAdd | dict[str, Any]) -> models.UpdateResult:
        """POST ProductionOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.ProductionOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST ProductionOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def replace_opr_tech_map(self, req: models.ProductionOperationReplaceOprTechMap | dict[str, Any]) -> models.UpdateResult:
        """POST ProductionOperation/ReplaceOprTechMap."""
        return await self._call(self.PATH_REPLACE_OPR_TECH_MAP, req, models.UpdateResult)

    async def delete(self, req: models.ProductionOperationDelete | dict[str, Any]) -> models.UpdateResult:
        """POST ProductionOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def move_operations(self, req: models.DocsOperationsMovement | dict[str, Any]) -> models.UpdateResult:
        """POST ProductionOperation/MoveOperations."""
        return await self._call(self.PATH_MOVE_OPERATIONS, req, models.UpdateResult)

__all__ = ['ProductionOperationService']
