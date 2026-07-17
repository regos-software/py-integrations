"""REGOS API service for UserNotify."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class UserNotifyService(RegosAPIService):
    PATH_GET = "UserNotify/Get"
    PATH_SET = "UserNotify/Set"
    REQUEST_MODELS = {
        'get': models.UserNotifyGet,
    }

    async def get(self, req: models.UserNotifyGet | dict[str, Any]) -> models.UserNotifyRegosArrayResult:
        """POST UserNotify/Get."""
        return await self._call(self.PATH_GET, req, models.UserNotifyRegosArrayResult)

    async def set(self, req: list[models.UserNotifySet] | list[dict[str, Any]]) -> models.UpdateResult:
        """POST UserNotify/Set."""
        return await self._call(self.PATH_SET, req, models.UpdateResult)

__all__ = ['UserNotifyService']
