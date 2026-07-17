"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ApplicationSetting(RegosModel):
    "Модель, описывающая настройку приложения"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID настройки (Устаревшее поле. Будет удалено после 16.03.2027)")
    app_id: int | None = PydField(default=None)
    key: str | None = PydField(default=None, description="Ключ настройки")
    dataType: DataType | None = PydField(default=None, description="4>")
    default_value: str | None = PydField(default=None)
    name_var: str | None = PydField(default=None, description="Наименование (ключ из переводов)")
    system: bool | None = PydField(default=None)
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи (Unix time, секунды)")


class ApplicationSettingAdd(RegosModel):
    "Модель добавления системной настройки приложения."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    app_id: int | None = PydField(default=None, description="ID приложения")
    key: str | None = PydField(default=None, description="Ключ настройки (до 200 символов, уникален в рамках app_id)")
    dataType: DataType | None = PydField(default=None, description="Тип данных: Integer, Float, String, DateTime")
    name_var: str | None = PydField(default=None, description="Ключ перевода (до 200 символов)")
    default_value: str | None = PydField(default=None, description="Значение по умолчанию")


class ApplicationSettingArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ApplicationSetting] | Error | None = PydField(default=None, description="Объект результата.")


class ApplicationSettingDelete(RegosModel):
    "Модель удаления системной настройки приложения."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    app_id: int | None = PydField(default=None, description="ID приложения")
    key: str | None = PydField(default=None, description="Ключ настройки (до 200 символов)")


class ApplicationSettingGet(RegosModel):
    "Модель получения системных настроек приложения."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    app_id: int | None = PydField(default=None, description="ID приложения")
    keys: list[str] | None = PydField(default=None, description="Ключи настроек")


class ApplicationSettingValue(RegosModel):
    "Значение настройки приложения для текущего пользователя."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID настройки")
    key: str | None = PydField(default=None, description="Ключ настройки")
    value: str | None = PydField(default=None, description="Значение")
    name: str | None = PydField(default=None, description="Наименование")
    name_var: str | None = PydField(default=None, description="Наименование (ключ из переводов)")
    dataType: DataType | None = PydField(default=None, description="Перечисление типов данных (используется в настройках)")
    last_update: int | None = PydField(default=None)


class ApplicationSettingValueArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ApplicationSettingValue] | Error | None = PydField(default=None, description="Объект результата.")


class ApplicationSettingValuesEdit(RegosModel):
    "Редактирование значений настроек приложения для текущего пользователя."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    app_id: int | None = PydField(default=None, description="ID приложения. Используется только если id не передан")
    id: int | None = PydField(default=None, description="Устаревшее поле. ID настройки. Будет удалено после 16.03.2027")
    key: str | None = PydField(default=None, description="Ключ настройки")
    value: str | None = PydField(default=None, description="Значение настройки")


class ApplicationSettingValuesGet(RegosModel):
    "Получение значений настроек приложения для текущего пользователя."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    app_id: int | None = PydField(default=None, description="ID приложения")
    ids: list[int] | None = PydField(default=None, description="Устаревшее поле. ID настроек. Будет удалено после 16.03.2027")
    keys: list[str] | None = PydField(default=None, description="Ключи настроек")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DataType, Error, InsertResult, UpdateResult


ApplicationSettingAddRequest: TypeAlias = ApplicationSettingAdd
ApplicationSettingAddResponse: TypeAlias = InsertResult
ApplicationSettingDeleteRequest: TypeAlias = ApplicationSettingDelete
ApplicationSettingDeleteResponse: TypeAlias = UpdateResult
ApplicationSettingEditValuesRequest: TypeAlias = list[ApplicationSettingValuesEdit]
ApplicationSettingEditValuesResponse: TypeAlias = UpdateResult
ApplicationSettingGetRequest: TypeAlias = ApplicationSettingGet
ApplicationSettingGetResponse: TypeAlias = ApplicationSettingArrayRegosObjectResult
ApplicationSettingGetValuesRequest: TypeAlias = ApplicationSettingValuesGet
ApplicationSettingGetValuesResponse: TypeAlias = ApplicationSettingValueArrayRegosObjectResult


_MODEL_NAMES = ['ApplicationSetting', 'ApplicationSettingAdd', 'ApplicationSettingArrayRegosObjectResult', 'ApplicationSettingDelete', 'ApplicationSettingGet', 'ApplicationSettingValue', 'ApplicationSettingValueArrayRegosObjectResult', 'ApplicationSettingValuesEdit', 'ApplicationSettingValuesGet']


__all__ = [
    'ApplicationSetting',
    'ApplicationSettingAdd',
    'ApplicationSettingArrayRegosObjectResult',
    'ApplicationSettingDelete',
    'ApplicationSettingGet',
    'ApplicationSettingValue',
    'ApplicationSettingValueArrayRegosObjectResult',
    'ApplicationSettingValuesEdit',
    'ApplicationSettingValuesGet',
    'ApplicationSettingGetValuesRequest',
    'ApplicationSettingGetValuesResponse',
    'ApplicationSettingEditValuesRequest',
    'ApplicationSettingEditValuesResponse',
    'ApplicationSettingAddRequest',
    'ApplicationSettingAddResponse',
    'ApplicationSettingGetRequest',
    'ApplicationSettingGetResponse',
    'ApplicationSettingDeleteRequest',
    'ApplicationSettingDeleteResponse'
]
