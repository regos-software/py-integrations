"""REGOS API service for WorkScheduleAssignment."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class WorkScheduleAssignmentService(RegosAPIService):
    PATH_GET_USERS = "WorkScheduleAssignment/GetUsers"
    PATH_GET_GROUPS = "WorkScheduleAssignment/GetGroups"
    PATH_SET_USERS = "WorkScheduleAssignment/SetUsers"
    PATH_SET_GROUPS = "WorkScheduleAssignment/SetGroups"
    PATH_DELETE_USER = "WorkScheduleAssignment/DeleteUser"
    PATH_DELETE_GROUP = "WorkScheduleAssignment/DeleteGroup"
    REQUEST_MODELS = {
        'delete_group': models.WorkScheduleAssignmentDeleteGroup,
        'delete_user': models.WorkScheduleAssignmentDeleteUser,
        'get_groups': models.WorkScheduleAssignmentGetGroups,
        'get_users': models.WorkScheduleAssignmentGetUsers,
        'set_groups': models.WorkScheduleAssignmentSetGroups,
        'set_users': models.WorkScheduleAssignmentSetUsers,
    }

    async def get_users(self, req: models.WorkScheduleAssignmentGetUsers | dict[str, Any]) -> models.WorkUserScheduleRegosOffsettedArrayResult:
        """POST WorkScheduleAssignment/GetUsers."""
        return await self._call(self.PATH_GET_USERS, req, models.WorkUserScheduleRegosOffsettedArrayResult)

    async def get_groups(self, req: models.WorkScheduleAssignmentGetGroups | dict[str, Any]) -> models.WorkGroupScheduleRegosOffsettedArrayResult:
        """POST WorkScheduleAssignment/GetGroups."""
        return await self._call(self.PATH_GET_GROUPS, req, models.WorkGroupScheduleRegosOffsettedArrayResult)

    async def set_users(self, req: models.WorkScheduleAssignmentSetUsers | dict[str, Any]) -> models.UpdateResult:
        """POST WorkScheduleAssignment/SetUsers."""
        return await self._call(self.PATH_SET_USERS, req, models.UpdateResult)

    async def set_groups(self, req: models.WorkScheduleAssignmentSetGroups | dict[str, Any]) -> models.UpdateResult:
        """POST WorkScheduleAssignment/SetGroups."""
        return await self._call(self.PATH_SET_GROUPS, req, models.UpdateResult)

    async def delete_user(self, req: models.WorkScheduleAssignmentDeleteUser | dict[str, Any]) -> models.UpdateResult:
        """POST WorkScheduleAssignment/DeleteUser."""
        return await self._call(self.PATH_DELETE_USER, req, models.UpdateResult)

    async def delete_group(self, req: models.WorkScheduleAssignmentDeleteGroup | dict[str, Any]) -> models.UpdateResult:
        """POST WorkScheduleAssignment/DeleteGroup."""
        return await self._call(self.PATH_DELETE_GROUP, req, models.UpdateResult)

__all__ = ['WorkScheduleAssignmentService']
