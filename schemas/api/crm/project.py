"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Project(RegosModel):
    "Модель, описывающая проект"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID проекта")
    name: str | None = PydField(default=None, description="Наименование проекта")
    description: str | None = PydField(default=None, description="Описание проекта")
    logo_file_id: int | None = PydField(default=None, description="ID файла логотипа проекта")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    access_all: bool | None = PydField(default=None, description="Признак доступа для всех пользователей")
    access_user_ids: list[int] | None = PydField(default=None, description="IDs пользователей с доступом")
    access_group_ids: list[int] | None = PydField(default=None, description="IDs групп пользователей с доступом")
    deleted: bool | None = PydField(default=None, description="Признак удаления проекта")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего проект")
    created_date: int | None = PydField(default=None, description="Дата создания проекта (Unix time, сек.)")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи (Unix time, сек.)")


class ProjectAdd(RegosModel):
    "Входная модель создания проекта."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование проекта")
    description: str | None = PydField(default=None, description="Описание проекта")
    logo_file_id: int | None = PydField(default=None, description="ID файла логотипа")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    access_all: bool | None = PydField(default=None, description="true — доступ всем пользователям")
    access_user_ids: list[int] | None = PydField(default=None, description="Список пользователей с доступом")
    access_group_ids: list[int] | None = PydField(default=None, description="Список групп с доступом")


class ProjectDelete(RegosModel):
    "Входная модель удаления проекта."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID проекта")


class ProjectEdit(RegosModel):
    "Входная модель изменения проекта."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID проекта")
    name: str | None = PydField(default=None, description="Новое наименование проекта")
    description: str | None = PydField(default=None, description="Новое описание проекта")
    logo_file_id: int | None = PydField(default=None, description="Новый ID файла логотипа; 0 — очистить")
    responsible_user_id: int | None = PydField(default=None, description="Новый ответственный")
    access_all: bool | None = PydField(default=None, description="Признак общего доступа")
    access_user_ids: list[int] | None = PydField(default=None, description="Новый список пользователей с доступом")
    access_group_ids: list[int] | None = PydField(default=None, description="Новый список групп с доступом")


class ProjectGet(RegosModel):
    "Входная модель фильтрации проектов."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID проектов")
    responsible_user_ids: list[int] | None = PydField(default=None, description="Фильтр по ответственным пользователям")
    search: str | None = PydField(default=None, description="Поиск по полям name и description")
    limit: int | None = PydField(default=None, description="Лимит элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")
    sort_orders: list[BaseSortColumn] | None = PydField(default=None, description="Параметры сортировки")


class ProjectRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Project] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ProjectSetAccess(RegosModel):
    "Входная модель назначения доступа к проекту."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID проекта")
    access_all: bool | None = PydField(default=None, description="true — доступ всем пользователям")
    access_user_ids: list[int] | None = PydField(default=None, description="IDs пользователей")
    access_group_ids: list[int] | None = PydField(default=None, description="IDs групп")
    replace_mode: bool | None = PydField(default=None, description="true — заменить текущие ACL, false — добавить к текущим")


class ProjectSetResponsible(RegosModel):
    "Входная модель смены ответственного проекта."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID проекта")
    responsible_user_id: int | None = PydField(default=None, description="ID нового ответственного")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BaseSortColumn, Error, InsertResult, UpdateResult


ProjectAddRequest: TypeAlias = ProjectAdd
ProjectAddResponse: TypeAlias = InsertResult
ProjectDeleteRequest: TypeAlias = ProjectDelete
ProjectDeleteResponse: TypeAlias = UpdateResult
ProjectEditRequest: TypeAlias = ProjectEdit
ProjectEditResponse: TypeAlias = UpdateResult
ProjectGetRequest: TypeAlias = ProjectGet
ProjectGetResponse: TypeAlias = ProjectRegosOffsettedArrayResult
ProjectSetAccessRequest: TypeAlias = ProjectSetAccess
ProjectSetAccessResponse: TypeAlias = UpdateResult
ProjectSetResponsibleRequest: TypeAlias = ProjectSetResponsible
ProjectSetResponsibleResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Project', 'ProjectAdd', 'ProjectDelete', 'ProjectEdit', 'ProjectGet', 'ProjectRegosOffsettedArrayResult', 'ProjectSetAccess', 'ProjectSetResponsible']


__all__ = [
    'Project',
    'ProjectAdd',
    'ProjectDelete',
    'ProjectEdit',
    'ProjectGet',
    'ProjectRegosOffsettedArrayResult',
    'ProjectSetAccess',
    'ProjectSetResponsible',
    'ProjectGetRequest',
    'ProjectGetResponse',
    'ProjectAddRequest',
    'ProjectAddResponse',
    'ProjectEditRequest',
    'ProjectEditResponse',
    'ProjectDeleteRequest',
    'ProjectDeleteResponse',
    'ProjectSetAccessRequest',
    'ProjectSetAccessResponse',
    'ProjectSetResponsibleRequest',
    'ProjectSetResponsibleResponse'
]
