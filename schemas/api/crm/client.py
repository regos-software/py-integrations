"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Client(RegosModel):
    "Модель клиента CRM"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID клиента")
    external_id: str | None = PydField(default=None, description="Внешний ID клиента")
    name: str | None = PydField(default=None, description="Имя клиента")
    phone: str | None = PydField(default=None, description="Телефон клиента")
    email: str | None = PydField(default=None, description="Email клиента")
    photo_url: str | None = PydField(default=None, description="Ссылка на аватар")
    description: str | None = PydField(default=None, description="Комментарий/описание")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    sentiment_score_avg: _Decimal | None = PydField(default=None, description="Средняя операторская оценка настроения клиента")
    sentiment_score_count: int | None = PydField(default=None, description="Количество оценок настроения клиента")
    sentiment_score_rolling_avg: _Decimal | None = PydField(default=None, description="Скользящая средняя оценка настроения клиента по последним обращениям")
    deleted: bool | None = PydField(default=None, description="Признак удаления (soft-delete)")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего клиента")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")
    fields: list[FieldValue] | None = PydField(default=None, description="Значения дополнительных полей")


class ClientAdd(RegosModel):
    "Request params for Client/Add."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    external_id: str | None = PydField(default=None, description="Внешний ID клиента")
    name: str | None = PydField(default=None, description="Имя клиента")
    phone: str | None = PydField(default=None, description="Телефон клиента")
    email: str | None = PydField(default=None, description="Email клиента")
    photo_url: str | None = PydField(default=None, description="Ссылка на аватар")
    description: str | None = PydField(default=None, description="Комментарий")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Значения дополнительных полей")


class ClientDelete(RegosModel):
    "Request params for Client/Delete."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID клиента")


class ClientEdit(RegosModel):
    "Request params for Client/Edit."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID клиента")
    external_id: str | None = PydField(default=None, description="Внешний ID клиента")
    name: str | None = PydField(default=None, description="Имя клиента")
    phone: str | None = PydField(default=None, description="Телефон клиента")
    email: str | None = PydField(default=None, description="Email клиента")
    photo_url: str | None = PydField(default=None, description="Ссылка на аватар")
    description: str | None = PydField(default=None, description="Комментарий")
    responsible_user_id: int | None = PydField(default=None, description="Не изменяется через Client/Edit; при передаче вернется 1008/responsible_user_id_use_setresponsible")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Изменение дополнительных полей")


class ClientGet(RegosModel):
    "Request params for Client/Get."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID клиентов")
    phones: list[str] | None = PydField(default=None, description="Фильтр по телефонам")
    external_ids: list[str] | None = PydField(default=None, description="Фильтр по внешним ID")
    emails: list[str] | None = PydField(default=None, description="Фильтр по email")
    search: str | None = PydField(default=None, description="Поиск по name, phone, email, external_id")
    responsible_user_ids: list[int] | None = PydField(default=None, description="Фильтр по ответственным пользователям")
    filters: list[Filter] | None = PydField(default=None, description="Дополнительные фильтры по стандартным и кастомным полям")
    limit: int | None = PydField(default=None, description="Лимит выборки. По умолчанию 100")
    offset: int | None = PydField(default=None, description="Смещение. По умолчанию 0")


class ClientMerge(RegosModel):
    "Request params for Client/Merge."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    source_client_id: int | None = PydField(default=None, description="ID клиента-источника (дубликат)")
    target_client_id: int | None = PydField(default=None, description="ID целевого клиента")
    comment: str | None = PydField(default=None, description="Комментарий к операции слияния")


class ClientRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Client] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ClientSetResponsible(RegosModel):
    "Request params for Client/SetResponsible."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID клиента")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit


ClientAddRequest: TypeAlias = ClientAdd
ClientAddResponse: TypeAlias = InsertResult
ClientDeleteRequest: TypeAlias = ClientDelete
ClientDeleteResponse: TypeAlias = UpdateResult
ClientEditRequest: TypeAlias = ClientEdit
ClientEditResponse: TypeAlias = UpdateResult
ClientGetRequest: TypeAlias = ClientGet
ClientGetResponse: TypeAlias = ClientRegosOffsettedArrayResult
ClientMergeRequest: TypeAlias = ClientMerge
ClientMergeResponse: TypeAlias = UpdateResult
ClientSetResponsibleRequest: TypeAlias = ClientSetResponsible
ClientSetResponsibleResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Client', 'ClientAdd', 'ClientDelete', 'ClientEdit', 'ClientGet', 'ClientMerge', 'ClientRegosOffsettedArrayResult', 'ClientSetResponsible']


__all__ = [
    'Client',
    'ClientAdd',
    'ClientDelete',
    'ClientEdit',
    'ClientGet',
    'ClientMerge',
    'ClientRegosOffsettedArrayResult',
    'ClientSetResponsible',
    'ClientGetRequest',
    'ClientGetResponse',
    'ClientAddRequest',
    'ClientAddResponse',
    'ClientEditRequest',
    'ClientEditResponse',
    'ClientDeleteRequest',
    'ClientDeleteResponse',
    'ClientSetResponsibleRequest',
    'ClientSetResponsibleResponse',
    'ClientMergeRequest',
    'ClientMergeResponse'
]
