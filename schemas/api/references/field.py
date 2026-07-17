"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Field(RegosModel):
    "Модель доп поля"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Идентификатор поля")
    key: str | None = PydField(default=None, description="Уникальный ключ поля (machine-name)")
    name: str | None = PydField(default=None, description="Читабельное наименование поля")
    entity_type: FieldEntityTypeEnum | None = PydField(default=None, description="Сущность, к которому привязано дополнительное поле")
    data_type: str | None = PydField(default=None, description="Тип данных значения поля. Допустимые значения: string, int, decimal, bool")
    metadata: str | None = PydField(default=None, description="Метаданные поля. Необязательное поле, максимум 500 символов с учётом экранирования")
    is_custom: bool | None = PydField(default=None, description="Признак: поле пользовательское (true) или системное (false)")
    required: bool | None = PydField(default=None, description="Обязательное поле (true) или нет (false)")


class FieldAdd(RegosModel):
    "Модель для добавления доп поля"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ поля (уникален в рамках entity_type), не более 30 символов. При сохранении к значению добавляется префикс field_")
    name: str | None = PydField(default=None, description="Наименование поля")
    entity_type: FieldEntityTypeEnum | None = PydField(default=None, description="Сущность, к которой привязано поле")
    data_type: str | None = PydField(default=None, description="Тип данных значения поля. Допустимые значения: string, int, decimal, bool")
    metadata: str | None = PydField(default=None, description="Метаданные поля. Максимальная длина — 500 символов с учётом экранирования. При null/пустом значении сохраняется null")
    required: bool | None = PydField(default=None, description="Обязательное поле (true) или нет (false). По умолчанию false")


class FieldEdit(RegosModel):
    "Модель для редактирования доп поля"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id поля")
    name: str | None = PydField(default=None, description="Наименование поля")
    required: bool | None = PydField(default=None, description="Обязательность поля для данных (true/false)")
    metadata: str | None = PydField(default=None, description="Метаданные поля. Максимальная длина — 500 символов с учётом экранирования")


class FieldEntityTypeEnum(str, Enum):
    "Перечисление сущностей данных доп полей"
    Default = "Default"
    RetailCustomer = "RetailCustomer"
    Partner = "Partner"
    DocPurchase = "DocPurchase"
    Item = "Item"
    DocPayment = "DocPayment"
    DocAccountMovement = "DocAccountMovement"
    Task = "Task"
    Lead = "Lead"
    Deal = "Deal"
    Client = "Client"
    Ticket = "Ticket"
    User = "User"


class FieldGet(RegosModel):
    "Модель доп поля"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id полей")
    keys: list[str] | None = PydField(default=None, description="Массив ключей (key) полей")
    entity_type: FieldEntityTypeEnum | None = PydField(default=None, description="Сущность, к которой привязано поле. Список допустимых значений")
    search: str | None = PydField(default=None, description="Строка поиска по полям name и key")
    sort_orders: list[BaseSortColumn] | None = PydField(default=None, description="Сортировка выходных параметров (по id, key, name)")
    required: bool | None = PydField(default=None, description="Фильтр по обязательности поля: true — обязательные, false — необязательные, null — все")


class FieldRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Field] | Error | None = PydField(default=None, description="Массив результата.")


class FieldValue(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    key: str | None = PydField(default=None, description="key поля")
    name: str | None = PydField(default=None, description="наименование поля")
    data_type: str | None = PydField(default=None, description="тип данных (допустимы string, int, decimal, bool)")
    metadata: str | None = PydField(default=None, description="метаданные поля")
    is_custom: bool | None = PydField(default=None, description="пользовательское поле (true) или нет (false)")
    required: bool | None = PydField(default=None, description="обязательно поле (true) или нет (false)")
    value: str | None = PydField(default=None, description="значение")


class FieldValueAdd(RegosModel):
    "Модель для добавления/редактирования значения доп поля"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="key поля")
    value: str | None = PydField(default=None, description="значение")


class FieldValueEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    deleted: bool | None = PydField(default=None, description="метка, что запись по доп полю нужно удалить")
    key: str | None = PydField(default=None, description="key поля")
    value: str | None = PydField(default=None, description="значение")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BaseSortColumn, Base_ID, Error, InsertResult, UpdateResult


FieldAddRequest: TypeAlias = FieldAdd
FieldAddResponse: TypeAlias = InsertResult
FieldDeleteRequest: TypeAlias = Base_ID
FieldDeleteResponse: TypeAlias = UpdateResult
FieldEditRequest: TypeAlias = FieldEdit
FieldEditResponse: TypeAlias = UpdateResult
FieldGetRequest: TypeAlias = FieldGet
FieldGetResponse: TypeAlias = FieldRegosArrayResult


_MODEL_NAMES = ['Field', 'FieldAdd', 'FieldEdit', 'FieldGet', 'FieldRegosArrayResult', 'FieldValue', 'FieldValueAdd', 'FieldValueEdit']


__all__ = [
    'Field',
    'FieldAdd',
    'FieldEdit',
    'FieldEntityTypeEnum',
    'FieldGet',
    'FieldRegosArrayResult',
    'FieldValue',
    'FieldValueAdd',
    'FieldValueEdit',
    'FieldGetRequest',
    'FieldGetResponse',
    'FieldAddRequest',
    'FieldAddResponse',
    'FieldEditRequest',
    'FieldEditResponse',
    'FieldDeleteRequest',
    'FieldDeleteResponse'
]
