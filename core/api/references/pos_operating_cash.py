"""REGOS API service for PosOperatingCash."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class PosOperatingCashService(RegosAPIService):
    PATH_GET_SETTINGS = "pos/OperatingCash/getSettings"
    REQUEST_MODELS = {
        'get_settings': models.OperatingCash_SettingGet,
    }

    async def get_settings(self, req: models.OperatingCash_SettingGet | dict[str, Any]) -> models.OperatingCash_SettingArrayRegosObjectResult:
        """POST pos/OperatingCash/getSettings."""
        return await self._call(self.PATH_GET_SETTINGS, req, models.OperatingCash_SettingArrayRegosObjectResult)

__all__ = ['PosOperatingCashService']
