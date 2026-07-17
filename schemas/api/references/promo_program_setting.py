"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PromoProgramSetting(RegosModel):
    "Модель, описывающая настройки промоакции"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id настройки промоакции")
    program_id: int | None = PydField(default=None, description="Id промоакции")
    program_type_id: int | None = PydField(default=None, description="Id типа промоакции")
    type: PromoProgramSettingType | None = PydField(default=None, description="Тип настройки: Client (Передаётся на кассы), Server (Настройка на стороне сервера)")
    key: str | None = PydField(default=None, description="Наименование настройки: general_settings, one_time_enrollment, one_time_withdrawal, birthday_enrollment,\nperiodically_enrollment, holiday_enrollment, item, item_group, setting_case, setting")
    value: str | None = PydField(default=None, description="Значение настройки")
    deleted: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class PromoProgramSettingAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    program_id: int | None = PydField(default=None, description="Id промоакции")
    key: str | None = PydField(default=None, description="Наименование настройки")
    value: str | None = PydField(default=None, description="Значение настройки")


class PromoProgramSettingArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PromoProgramSetting] | Error | None = PydField(default=None, description="Объект результата.")


class PromoProgramSettingDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id настройки промоакции")


class PromoProgramSettingEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id настройки промоакции")
    value: str | None = PydField(default=None, description="Значение настройки")


class PromoProgramSettingGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id настройки промоакции")
    ids: list[int] | None = PydField(default=None, description="массив id настроек промоакции")
    type_ids: list[int] | None = PydField(default=None, description="массив id типов промоакции")
    program_id: int | None = PydField(default=None, description="id промоакции")
    program_ids: list[int] | None = PydField(default=None, description="массив id промоакций")
    key: str | None = PydField(default=None, description="Наименование настройки")


class PromoProgramSettingType(str, Enum):
    Default = "Default"
    Client = "Client"
    Server = "Server"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


PromoProgramSettingAddRequest: TypeAlias = list[PromoProgramSettingAdd]
PromoProgramSettingAddResponse: TypeAlias = InsertResult
PromoProgramSettingAddSingleRequest: TypeAlias = PromoProgramSettingAdd
PromoProgramSettingAddSingleResponse: TypeAlias = InsertResult
PromoProgramSettingDeleteRequest: TypeAlias = PromoProgramSettingDelete
PromoProgramSettingDeleteResponse: TypeAlias = UpdateResult
PromoProgramSettingEditRequest: TypeAlias = list[PromoProgramSettingEdit]
PromoProgramSettingEditResponse: TypeAlias = UpdateResult
PromoProgramSettingGetRequest: TypeAlias = PromoProgramSettingGet
PromoProgramSettingGetResponse: TypeAlias = PromoProgramSettingArrayRegosObjectResult


_MODEL_NAMES = ['PromoProgramSetting', 'PromoProgramSettingAdd', 'PromoProgramSettingArrayRegosObjectResult', 'PromoProgramSettingDelete', 'PromoProgramSettingEdit', 'PromoProgramSettingGet']


__all__ = [
    'PromoProgramSetting',
    'PromoProgramSettingAdd',
    'PromoProgramSettingArrayRegosObjectResult',
    'PromoProgramSettingDelete',
    'PromoProgramSettingEdit',
    'PromoProgramSettingGet',
    'PromoProgramSettingType',
    'PromoProgramSettingGetRequest',
    'PromoProgramSettingGetResponse',
    'PromoProgramSettingAddSingleRequest',
    'PromoProgramSettingAddSingleResponse',
    'PromoProgramSettingAddRequest',
    'PromoProgramSettingAddResponse',
    'PromoProgramSettingEditRequest',
    'PromoProgramSettingEditResponse',
    'PromoProgramSettingDeleteRequest',
    'PromoProgramSettingDeleteResponse'
]
