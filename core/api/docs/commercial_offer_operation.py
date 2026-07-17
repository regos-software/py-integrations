"""REGOS API service for CommercialOfferOperation."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class CommercialOfferOperationService(RegosAPIService):
    PATH_GET = "CommercialOfferOperation/Get"
    PATH_ADD = "CommercialOfferOperation/Add"
    PATH_EDIT = "CommercialOfferOperation/Edit"
    PATH_DELETE = "CommercialOfferOperation/Delete"
    REQUEST_MODELS = {
        'get': models.CommercialOfferOperationGet,
    }

    async def get(self, req: models.CommercialOfferOperationGet | dict[str, Any]) -> models.CommercialOfferOperationRegosOffsettedArrayResult:
        """POST CommercialOfferOperation/Get."""
        return await self._call(self.PATH_GET, req, models.CommercialOfferOperationRegosOffsettedArrayResult)

    async def add(self, req: list[models.CommercialOfferOperationAdd] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST CommercialOfferOperation/Add."""
        return await self._call(self.PATH_ADD, req, models.UpdateResult)

    async def edit(self, req: list[models.CommercialOfferOperationEdit] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST CommercialOfferOperation/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: list[models.CommercialOfferOperationDelete] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST CommercialOfferOperation/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['CommercialOfferOperationService']
