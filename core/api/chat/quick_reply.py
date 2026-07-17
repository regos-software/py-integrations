"""REGOS API service for QuickReply."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class QuickReplyService(RegosAPIService):
    PATH_GET = "QuickReply/Get"
    PATH_ADD = "QuickReply/Add"
    PATH_DELETE = "QuickReply/Delete"
    REQUEST_MODELS = {
        'add': models.QuickReplyAdd,
        'delete': models.QuickReplyDelete,
        'get': models.QuickReplyGet,
    }

    async def get(self, req: models.QuickReplyGet | dict[str, Any]) -> models.QuickReplyRegosOffsettedArrayResult:
        """POST QuickReply/Get."""
        return await self._call(self.PATH_GET, req, models.QuickReplyRegosOffsettedArrayResult)

    async def add(self, req: models.QuickReplyAdd | dict[str, Any]) -> models.InsertResult:
        """POST QuickReply/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def delete(self, req: models.QuickReplyDelete | dict[str, Any]) -> models.UpdateResult:
        """POST QuickReply/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['QuickReplyService']
