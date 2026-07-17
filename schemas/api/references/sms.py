"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class SingleSms(RegosModel):
    "Класс, представляющий единичное SMS-сообщение"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Уникальный идентификатор SMS-сообщения")
    entity_type: SingleSmsEntityTypeEnum | None = PydField(default=None, description="Тип сущности получателя СМС")
    entity_id: int | None = PydField(default=None, description="ID сщности получателя смс")
    date: int | None = PydField(default=None, description="Дата и время создания сообщения (в формате Unix Timestamp)")
    status: SingleSmsStatusEnum | None = PydField(default=None, description="Текущий статус SMS-сообщения")
    phone: str | None = PydField(default=None)
    message: str | None = PydField(default=None, description="Текст SMS-сообщения")
    last_update: int | None = PydField(default=None, description="Время последнего обновления (в формате Unix Timestamp)")


class SingleSmsAdd(RegosModel):
    "Добавление единичной СМС"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    entity_type: SingleSmsEntityTypeEnum | None = PydField(default=None, description="Получатель СМС сообщения: <RetailCustomer | 1> - Розничный покупатель, <Partner | 2> - Контрагент")
    entity_id: int | None = PydField(default=None, description="ID получателя СМС сообщения")
    message: str | None = PydField(default=None, description="Текст СМС сообщения")


class SingleSmsEntityTypeEnum(str, Enum):
    "Перечисление сущностей получателей СМС"
    Default = "Default"
    RetailCustomer = "RetailCustomer"
    Partner = "Partner"


class SingleSmsGet(RegosModel):
    "Получить список единичных СМС"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID единичных СМС")
    entity_type: SingleSmsEntityTypeEnum | None = PydField(default=None, description="Тип получателя СМС: <RetailCustomer | 1> - Розничный покупатель, <Partner | 2> - Контрагент")
    entity_id: int | None = PydField(default=None, description="ID получателя СМС")
    status: SingleSmsStatusEnum | None = PydField(default=None, description="Статус отправки СМС: <New | 1> - Создано, <Sended | 2> - Отправлено, <Delivered | 3> - Доставлено, <Error | 4> - Ошибка отправки")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class SingleSmsRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[SingleSms] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class SingleSmsSetStatus(RegosModel):
    "Установка статуса единичного смс"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID СМС сообщения")
    status: SingleSmsStatusEnum | None = PydField(default=None, description="Статусы СМС сообщения: <New | 1> - Создано, <Sended | 2> - Отправлено, <Delivered | 3> - Доставлено, <Error | 4> - Ошибка отправки")
    error_message: str | None = PydField(default=None, description="Сообщение об ошибке")


class SingleSmsStatusEnum(str, Enum):
    "Перечисление статусов единичных SMS-сообщений"
    Default = "Default"
    New = "New"
    Sended = "Sended"
    Delivered = "Delivered"
    Error = "Error"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, ObjectRegosObjectResult


SmsAddRequest: TypeAlias = SingleSmsAdd
SmsAddResponse: TypeAlias = InsertResult
SmsGetRequest: TypeAlias = SingleSmsGet
SmsGetResponse: TypeAlias = SingleSmsRegosOffsettedArrayResult
SmsSetStatusRequest: TypeAlias = SingleSmsSetStatus
SmsSetStatusResponse: TypeAlias = ObjectRegosObjectResult


_MODEL_NAMES = ['SingleSms', 'SingleSmsAdd', 'SingleSmsGet', 'SingleSmsRegosOffsettedArrayResult', 'SingleSmsSetStatus']


__all__ = [
    'SingleSms',
    'SingleSmsAdd',
    'SingleSmsEntityTypeEnum',
    'SingleSmsGet',
    'SingleSmsRegosOffsettedArrayResult',
    'SingleSmsSetStatus',
    'SingleSmsStatusEnum',
    'SmsGetRequest',
    'SmsGetResponse',
    'SmsAddRequest',
    'SmsAddResponse',
    'SmsSetStatusRequest',
    'SmsSetStatusResponse'
]
