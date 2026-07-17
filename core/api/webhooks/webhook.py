"""REGOS API service for Webhook."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class WebhookService(RegosAPIService):
    PATH_GET = "Webhook/Get"

    async def get(self, body: dict[str, Any] | None = None) -> models.StringRegosArrayResult:
        """POST Webhook/Get."""
        return await self._call(self.PATH_GET, body or {}, models.StringRegosArrayResult)

__all__ = ['WebhookService']
