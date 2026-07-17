"""REGOS API service for DocumentEnumerator."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class DocumentEnumeratorService(RegosAPIService):
    PATH_GET = "DocumentEnumerator/Get"
    PATH_EDIT = "DocumentEnumerator/Edit"
    PATH_RESET = "DocumentEnumerator/Reset"
    REQUEST_MODELS = {
        'edit': models.DocEnumeratorEdit,
        'get': models.DocEnumeratorGet,
        'reset': models.DocEnumeratorReset,
    }

    async def get(self, req: models.DocEnumeratorGet | dict[str, Any]) -> models.DocEnumeratorRegosArrayResult:
        """POST DocumentEnumerator/Get."""
        return await self._call(self.PATH_GET, req, models.DocEnumeratorRegosArrayResult)

    async def edit(self, req: models.DocEnumeratorEdit | dict[str, Any]) -> models.UpdateResult:
        """POST DocumentEnumerator/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def reset(self, req: models.DocEnumeratorReset | dict[str, Any]) -> models.UpdateResult:
        """POST DocumentEnumerator/Reset."""
        return await self._call(self.PATH_RESET, req, models.UpdateResult)

__all__ = ['DocumentEnumeratorService']
