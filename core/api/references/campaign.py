"""REGOS API service for Campaign."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class CampaignService(RegosAPIService):
    PATH_GET = "Campaign/Get"
    PATH_ADD = "Campaign/Add"
    PATH_EDIT = "Campaign/Edit"
    PATH_DELETE = "Campaign/Delete"
    PATH_SET_STATUS = "Campaign/SetStatus"
    PATH_GET_RECIPIENTS = "Campaign/GetRecipients"
    PATH_SET_RECIPIENTS_STATUS = "Campaign/SetRecipientsStatus"
    REQUEST_MODELS = {
        'add': models.CampaignAdd,
        'delete': models.Base_ID,
        'edit': models.CampaignEdit,
        'get': models.CampaignGet,
        'get_recipients': models.CampaignRecipientsGet,
        'set_status': models.CampaignSetStatus,
    }

    async def get(self, req: models.CampaignGet | dict[str, Any]) -> models.CampaignRegosOffsettedArrayResult:
        """POST Campaign/Get."""
        return await self._call(self.PATH_GET, req, models.CampaignRegosOffsettedArrayResult)

    async def add(self, req: models.CampaignAdd | dict[str, Any]) -> models.InsertResult:
        """POST Campaign/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.CampaignEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Campaign/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST Campaign/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def set_status(self, req: models.CampaignSetStatus | dict[str, Any]) -> models.UpdateResult:
        """POST Campaign/SetStatus."""
        return await self._call(self.PATH_SET_STATUS, req, models.UpdateResult)

    async def get_recipients(self, req: models.CampaignRecipientsGet | dict[str, Any]) -> models.CampaignRecipientRegosOffsettedArrayResult:
        """POST Campaign/GetRecipients."""
        return await self._call(self.PATH_GET_RECIPIENTS, req, models.CampaignRecipientRegosOffsettedArrayResult)

    async def set_recipients_status(self, req: list[models.CampaignRecipientSetStatus] | list[dict[str, Any]]) -> models.SingleObjectResult:
        """POST Campaign/SetRecipientsStatus."""
        return await self._call(self.PATH_SET_RECIPIENTS_STATUS, req, models.SingleObjectResult)

__all__ = ['CampaignService']
