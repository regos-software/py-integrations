"""REGOS API service for PartnerGroup."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PartnerGroupService(RegosAPIService):
    PATH_GET = "PartnerGroup/Get"
    PATH_ADD = "PartnerGroup/Add"
    PATH_EDIT = "PartnerGroup/Edit"
    PATH_DELETE = "PartnerGroup/Delete"
    REQUEST_MODELS = {
        'add': models.PartnerGroupAdd,
        'delete': models.PartnerGroupDelete,
        'edit': models.PartnerGroupEdit,
        'get': models.PartnerGroupGet,
    }

    async def get(self, req: models.PartnerGroupGet | dict[str, Any]) -> models.PartnerGroupArrayRegosObjectResult:
        """POST PartnerGroup/Get."""
        return await self._call(self.PATH_GET, req, models.PartnerGroupArrayRegosObjectResult)

    async def add(self, req: models.PartnerGroupAdd | dict[str, Any]) -> models.InsertResult:
        """POST PartnerGroup/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.PartnerGroupEdit | dict[str, Any]) -> models.UpdateResult:
        """POST PartnerGroup/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.PartnerGroupDelete | dict[str, Any]) -> models.UpdateResult:
        """POST PartnerGroup/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['PartnerGroupService']
