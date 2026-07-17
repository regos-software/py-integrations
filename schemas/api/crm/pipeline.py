"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Pipeline(RegosModel):
    "Модели Pipeline"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID воронки")
    entity_type: CrmEntityTypeEnum | None = PydField(default=None, description="Тип сущности: Lead или Deal")
    name: str | None = PydField(default=None, description="Название воронки")
    is_default: bool | None = PydField(default=None, description="Признак воронки по умолчанию для типа сущности")
    access_all: bool | None = PydField(default=None, description="Признак доступа для всех пользователей")
    access_user_ids: list[int] | None = PydField(default=None, description="IDs пользователей с доступом")
    access_group_ids: list[int] | None = PydField(default=None, description="IDs групп пользователей с доступом")
    active: bool | None = PydField(default=None, description="Признак активности")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")
    stages: list[Stage] | None = PydField(default=None, description="Набор стадий воронки")


class PipelineAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    entity_type: CrmEntityTypeEnum | None = PydField(default=None, description="Тип сущности: Lead, Deal")
    name: str | None = PydField(default=None, description="Название воронки")
    is_default: bool | None = PydField(default=None, description="Признак воронки по умолчанию для типа сущности")
    access_all: bool | None = PydField(default=None, description="Доступ для всех пользователей")
    access_user_ids: list[int] | None = PydField(default=None, description="Явный список пользователей с доступом")
    access_group_ids: list[int] | None = PydField(default=None, description="Явный список групп с доступом")
    active: bool | None = PydField(default=None, description="Признак активности воронки")


class PipelineDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID воронки")


class PipelineEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID воронки")
    name: str | None = PydField(default=None, description="Новое название; если передано, не может быть пустой строкой")
    is_default: bool | None = PydField(default=None, description="Признак воронки по умолчанию")
    active: bool | None = PydField(default=None, description="Признак активности")


class PipelineGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    entity_type: CrmEntityTypeEnum | None = PydField(default=None, description="Тип сущности: Lead, Deal")
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID воронок")
    active: bool | None = PydField(default=None, description="Фильтр по активности")
    limit: int | None = PydField(default=None, description="Лимит выборки, при <= 0 используется 100, максимум 1000")
    offset: int | None = PydField(default=None, description="Смещение выборки, при < 0 используется 0")


class PipelineRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Pipeline] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class PipelineSetAccess(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID воронки")
    access_all: bool | None = PydField(default=None, description="Доступ для всех пользователей")
    access_user_ids: list[int] | None = PydField(default=None, description="Список пользователей")
    access_group_ids: list[int] | None = PydField(default=None, description="Список групп")
    replace_mode: bool | None = PydField(default=None, description="Режим обновления ACL: true — полная замена, false — добавление к текущему списку")


class PipelineSetStage(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    name: str | None = PydField(default=None)
    code: str | None = PydField(default=None)
    sort_order: int | None = PydField(default=None)
    is_start: bool | None = PydField(default=None)
    is_terminal: bool | None = PydField(default=None)
    is_success: bool | None = PydField(default=None)
    active: bool | None = PydField(default=None)


class PipelineSetStages(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    pipeline_id: int | None = PydField(default=None, description="ID воронки")
    stages: list[PipelineSetStage] | None = PydField(default=None, description="Набор стадий для upsert")


class Stage(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    pipeline_id: int | None = PydField(default=None)
    name: str | None = PydField(default=None)
    code: str | None = PydField(default=None)
    sort_order: int | None = PydField(default=None)
    is_start: bool | None = PydField(default=None)
    is_terminal: bool | None = PydField(default=None)
    is_success: bool | None = PydField(default=None)
    active: bool | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import CrmEntityTypeEnum, Error, InsertResult, UpdateResult


CrmEntityTypeEnum: TypeAlias = CrmEntityTypeEnum
PipelineAddRequest: TypeAlias = PipelineAdd
PipelineAddResponse: TypeAlias = InsertResult
PipelineDeleteRequest: TypeAlias = PipelineDelete
PipelineDeleteResponse: TypeAlias = UpdateResult
PipelineEditRequest: TypeAlias = PipelineEdit
PipelineEditResponse: TypeAlias = UpdateResult
PipelineGetRequest: TypeAlias = PipelineGet
PipelineGetResponse: TypeAlias = PipelineRegosOffsettedArrayResult
PipelineSetAccessRequest: TypeAlias = PipelineSetAccess
PipelineSetAccessResponse: TypeAlias = UpdateResult
PipelineSetStagesRequest: TypeAlias = PipelineSetStages
PipelineSetStagesResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Pipeline', 'PipelineAdd', 'PipelineDelete', 'PipelineEdit', 'PipelineGet', 'PipelineRegosOffsettedArrayResult', 'PipelineSetAccess', 'PipelineSetStage', 'PipelineSetStages', 'Stage']


__all__ = [
    'Pipeline',
    'PipelineAdd',
    'PipelineDelete',
    'PipelineEdit',
    'PipelineGet',
    'PipelineRegosOffsettedArrayResult',
    'PipelineSetAccess',
    'PipelineSetStage',
    'PipelineSetStages',
    'Stage',
    'PipelineGetRequest',
    'PipelineGetResponse',
    'PipelineAddRequest',
    'PipelineAddResponse',
    'PipelineEditRequest',
    'PipelineEditResponse',
    'PipelineSetAccessRequest',
    'PipelineSetAccessResponse',
    'PipelineDeleteRequest',
    'PipelineDeleteResponse',
    'PipelineSetStagesRequest',
    'PipelineSetStagesResponse',
    'CrmEntityTypeEnum'
]
