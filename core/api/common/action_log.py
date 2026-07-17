"""REGOS API service for ActionLog."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ActionLogService(RegosAPIService):
    PATH_GET = "ActionLog/Get"
    REQUEST_MODELS = {
        'get': models.ActionlogGet,
    }

    async def get(self, req: models.ActionlogGet | dict[str, Any]) -> models.ActionlogRegosOffsettedArrayResult:
        """POST ActionLog/Get."""
        return await self._call(self.PATH_GET, req, models.ActionlogRegosOffsettedArrayResult)

__all__ = ['ActionLogService']
