"""REGOS API service for Sms."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class SmsService(RegosAPIService):
    PATH_GET = "Sms/Get"
    PATH_ADD = "Sms/Add"
    PATH_SET_STATUS = "Sms/SetStatus"
    REQUEST_MODELS = {
        'add': models.SingleSmsAdd,
        'get': models.SingleSmsGet,
        'set_status': models.SingleSmsSetStatus,
    }

    async def get(self, req: models.SingleSmsGet | dict[str, Any]) -> models.SingleSmsRegosOffsettedArrayResult:
        """POST Sms/Get."""
        return await self._call(self.PATH_GET, req, models.SingleSmsRegosOffsettedArrayResult)

    async def add(self, req: models.SingleSmsAdd | dict[str, Any]) -> models.InsertResult:
        """POST Sms/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def set_status(self, req: models.SingleSmsSetStatus | dict[str, Any]) -> models.ObjectRegosObjectResult:
        """POST Sms/SetStatus."""
        return await self._call(self.PATH_SET_STATUS, req, models.ObjectRegosObjectResult)

__all__ = ['SmsService']
