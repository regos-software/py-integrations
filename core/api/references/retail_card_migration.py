"""REGOS API service for RetailCardMigration."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class RetailCardMigrationService(RegosAPIService):
    PATH_TASKS_GET = "RetailCardMigration/Tasks/Get"
    PATH_TASKS_ADD = "RetailCardMigration/Tasks/Add"
    PATH_TASKS_EDIT = "RetailCardMigration/Tasks/Edit"
    PATH_TASKS_DELETE = "RetailCardMigration/Tasks/Delete"
    PATH_SETTINGS_GET = "RetailCardMigration/Settings/Get"
    PATH_SETTINGS_ADD = "RetailCardMigration/Settings/Add"
    PATH_SETTINGS_EDIT = "RetailCardMigration/Settings/Edit"
    PATH_SETTINGS_DELETE = "RetailCardMigration/Settings/Delete"
    PATH_SETTING_CONDITION_GET = "RetailCardMigration/SettingCondition/Get"
    PATH_SETTING_CONDITION_ADD = "RetailCardMigration/SettingCondition/Add"
    PATH_SETTING_CONDITION_DELETE = "RetailCardMigration/SettingCondition/Delete"
    REQUEST_MODELS = {
        'setting_condition_add': models.RetailCardMigrationSettingConditionBase,
        'setting_condition_delete': models.Base_ID,
        'setting_condition_get': models.RetailCardMigrationSettingConditionGet,
        'settings_add': models.RetailCardMigrationSettingBase,
        'settings_delete': models.Base_ID,
        'settings_edit': models.RetailCardMigrationSettingEdit,
        'settings_get': models.RetailCardMigrationSettingGet,
        'tasks_add': models.RetailCardMigrationTaskAdd,
        'tasks_delete': models.Base_ID,
        'tasks_edit': models.RetailCardMigrationTaskEdit,
        'tasks_get': models.RetailCardMigrationTaskGet,
    }

    async def tasks_get(self, req: models.RetailCardMigrationTaskGet | dict[str, Any]) -> models.RetailCardMigrationTaskRegosOffsettedArrayResult:
        """POST RetailCardMigration/Tasks/Get."""
        return await self._call(self.PATH_TASKS_GET, req, models.RetailCardMigrationTaskRegosOffsettedArrayResult)

    async def tasks_add(self, req: models.RetailCardMigrationTaskAdd | dict[str, Any]) -> models.InsertResult:
        """POST RetailCardMigration/Tasks/Add."""
        return await self._call(self.PATH_TASKS_ADD, req, models.InsertResult)

    async def tasks_edit(self, req: models.RetailCardMigrationTaskEdit | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCardMigration/Tasks/Edit."""
        return await self._call(self.PATH_TASKS_EDIT, req, models.UpdateResult)

    async def tasks_delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCardMigration/Tasks/Delete."""
        return await self._call(self.PATH_TASKS_DELETE, req, models.UpdateResult)

    async def settings_get(self, req: models.RetailCardMigrationSettingGet | dict[str, Any]) -> models.RetailCardMigrationSettingRegosOffsettedArrayResult:
        """POST RetailCardMigration/Settings/Get."""
        return await self._call(self.PATH_SETTINGS_GET, req, models.RetailCardMigrationSettingRegosOffsettedArrayResult)

    async def settings_add(self, req: models.RetailCardMigrationSettingBase | dict[str, Any]) -> models.InsertResult:
        """POST RetailCardMigration/Settings/Add."""
        return await self._call(self.PATH_SETTINGS_ADD, req, models.InsertResult)

    async def settings_edit(self, req: models.RetailCardMigrationSettingEdit | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCardMigration/Settings/Edit."""
        return await self._call(self.PATH_SETTINGS_EDIT, req, models.UpdateResult)

    async def settings_delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCardMigration/Settings/Delete."""
        return await self._call(self.PATH_SETTINGS_DELETE, req, models.UpdateResult)

    async def setting_condition_get(self, req: models.RetailCardMigrationSettingConditionGet | dict[str, Any]) -> models.RetailCardMigrationSettingConditionRegosOffsettedArrayResult:
        """POST RetailCardMigration/SettingCondition/Get."""
        return await self._call(self.PATH_SETTING_CONDITION_GET, req, models.RetailCardMigrationSettingConditionRegosOffsettedArrayResult)

    async def setting_condition_add(self, req: models.RetailCardMigrationSettingConditionBase | dict[str, Any]) -> models.InsertResult:
        """POST RetailCardMigration/SettingCondition/Add."""
        return await self._call(self.PATH_SETTING_CONDITION_ADD, req, models.InsertResult)

    async def setting_condition_delete(self, req: models.Base_ID | dict[str, Any]) -> models.UpdateResult:
        """POST RetailCardMigration/SettingCondition/Delete."""
        return await self._call(self.PATH_SETTING_CONDITION_DELETE, req, models.UpdateResult)

__all__ = ['RetailCardMigrationService']
