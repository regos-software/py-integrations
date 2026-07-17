"""REGOS API service for PrintFormType."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PrintFormTypeService(RegosAPIService):
    PATH_GET = "PrintFormType/Get"
    PATH_SET = "PrintFormType/Set"
    PATH_REMOVE = "PrintFormType/Remove"
    REQUEST_MODELS = {
        'get': models.PrintFormTypeGet,
        'remove': models.PrintFormTypeRemove,
        'set': models.PrintFormTypeSet,
    }

    async def get(self, req: models.PrintFormTypeGet | dict[str, Any]) -> models.PrintFormTypeRegosArrayResult:
        """POST PrintFormType/Get."""
        return await self._call(self.PATH_GET, req, models.PrintFormTypeRegosArrayResult)

    async def set(self, req: models.PrintFormTypeSet | dict[str, Any]) -> models.InsertResult:
        """POST PrintFormType/Set."""
        return await self._call(self.PATH_SET, req, models.InsertResult)

    async def remove(self, req: models.PrintFormTypeRemove | dict[str, Any]) -> models.UpdateResult:
        """POST PrintFormType/Remove."""
        return await self._call(self.PATH_REMOVE, req, models.UpdateResult)

__all__ = ['PrintFormTypeService']
