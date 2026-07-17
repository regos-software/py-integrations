"""REGOS API service for IntegrationWebhook."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class IntegrationWebhookService(RegosAPIService):
    PATH_GET = "IntegrationWebhook/Get"

    async def get(self, body: dict[str, Any] | None = None) -> models.IntegrationWebhookRegosArrayResult:
        """POST IntegrationWebhook/Get."""
        return await self._call(self.PATH_GET, body or {}, models.IntegrationWebhookRegosArrayResult)

__all__ = ['IntegrationWebhookService']
