"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class WorkGroupSchedule(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    group_id: int | None = PydField(default=None)
    schedule_id: int | None = PydField(default=None)
    date_from: str | None = PydField(default=None)
    date_to: str | None = PydField(default=None)
    priority: int | None = PydField(default=None)
    active: bool | None = PydField(default=None)
    created_user_id: int | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class WorkGroupScheduleRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[WorkGroupSchedule] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class WorkGroupScheduleSetItem(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    group_id: int | None = PydField(default=None)
    schedule_id: int | None = PydField(default=None)
    date_from: str | None = PydField(default=None)
    date_to: str | None = PydField(default=None)
    priority: int | None = PydField(default=None)


class WorkScheduleAssignmentDeleteGroup(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID назначения")


class WorkScheduleAssignmentDeleteUser(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID назначения")


class WorkScheduleAssignmentGetGroups(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    group_ids: list[int] | None = PydField(default=None, description="Массив ID групп")
    date: str | None = PydField(default=None, description="Дата фильтра YYYY-MM-DD")
    limit: int | None = PydField(default=None, description="Лимит выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")


class WorkScheduleAssignmentGetUsers(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_ids: list[int] | None = PydField(default=None, description="Массив ID пользователей")
    schedule_ids: list[int] | None = PydField(default=None, description="Массив ID графиков")
    active: bool | None = PydField(default=None, description="Фильтр по актуальности назначения")
    date: str | None = PydField(default=None, description="Дата фильтра YYYY-MM-DD")
    limit: int | None = PydField(default=None, description="Лимит выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")


class WorkScheduleAssignmentSetGroups(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    assignments: list[WorkGroupScheduleSetItem] | None = PydField(default=None, description="Список назначений групп")


class WorkScheduleAssignmentSetUsers(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    assignments: list[WorkUserScheduleSetItem] | None = PydField(default=None, description="Список назначений пользователей")


class WorkUserSchedule(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    user_id: int | None = PydField(default=None)
    schedule_id: int | None = PydField(default=None)
    date_from: str | None = PydField(default=None)
    date_to: str | None = PydField(default=None)
    active: bool | None = PydField(default=None)
    created_user_id: int | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class WorkUserScheduleRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[WorkUserSchedule] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class WorkUserScheduleSetItem(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None)
    schedule_id: int | None = PydField(default=None)
    date_from: str | None = PydField(default=None)
    date_to: str | None = PydField(default=None)


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, UpdateResult


WorkScheduleAssignmentDeleteGroupRequest: TypeAlias = WorkScheduleAssignmentDeleteGroup
WorkScheduleAssignmentDeleteGroupResponse: TypeAlias = UpdateResult
WorkScheduleAssignmentDeleteUserRequest: TypeAlias = WorkScheduleAssignmentDeleteUser
WorkScheduleAssignmentDeleteUserResponse: TypeAlias = UpdateResult
WorkScheduleAssignmentGetGroupsRequest: TypeAlias = WorkScheduleAssignmentGetGroups
WorkScheduleAssignmentGetGroupsResponse: TypeAlias = WorkGroupScheduleRegosOffsettedArrayResult
WorkScheduleAssignmentGetUsersRequest: TypeAlias = WorkScheduleAssignmentGetUsers
WorkScheduleAssignmentGetUsersResponse: TypeAlias = WorkUserScheduleRegosOffsettedArrayResult
WorkScheduleAssignmentSetGroupsRequest: TypeAlias = WorkScheduleAssignmentSetGroups
WorkScheduleAssignmentSetGroupsResponse: TypeAlias = UpdateResult
WorkScheduleAssignmentSetUsersRequest: TypeAlias = WorkScheduleAssignmentSetUsers
WorkScheduleAssignmentSetUsersResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['WorkGroupSchedule', 'WorkGroupScheduleRegosOffsettedArrayResult', 'WorkGroupScheduleSetItem', 'WorkScheduleAssignmentDeleteGroup', 'WorkScheduleAssignmentDeleteUser', 'WorkScheduleAssignmentGetGroups', 'WorkScheduleAssignmentGetUsers', 'WorkScheduleAssignmentSetGroups', 'WorkScheduleAssignmentSetUsers', 'WorkUserSchedule', 'WorkUserScheduleRegosOffsettedArrayResult', 'WorkUserScheduleSetItem']


__all__ = [
    'WorkGroupSchedule',
    'WorkGroupScheduleRegosOffsettedArrayResult',
    'WorkGroupScheduleSetItem',
    'WorkScheduleAssignmentDeleteGroup',
    'WorkScheduleAssignmentDeleteUser',
    'WorkScheduleAssignmentGetGroups',
    'WorkScheduleAssignmentGetUsers',
    'WorkScheduleAssignmentSetGroups',
    'WorkScheduleAssignmentSetUsers',
    'WorkUserSchedule',
    'WorkUserScheduleRegosOffsettedArrayResult',
    'WorkUserScheduleSetItem',
    'WorkScheduleAssignmentGetUsersRequest',
    'WorkScheduleAssignmentGetUsersResponse',
    'WorkScheduleAssignmentGetGroupsRequest',
    'WorkScheduleAssignmentGetGroupsResponse',
    'WorkScheduleAssignmentSetUsersRequest',
    'WorkScheduleAssignmentSetUsersResponse',
    'WorkScheduleAssignmentSetGroupsRequest',
    'WorkScheduleAssignmentSetGroupsResponse',
    'WorkScheduleAssignmentDeleteUserRequest',
    'WorkScheduleAssignmentDeleteUserResponse',
    'WorkScheduleAssignmentDeleteGroupRequest',
    'WorkScheduleAssignmentDeleteGroupResponse'
]
