"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class IntegrationConnect(RegosModel):
    "Модель для подключения интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ (системное название) интеграции")


class IntegrationConnected(RegosModel):
    "Модель описывающая подключённую интеграцию"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    name: str | None = PydField(default=None, description="Название интеграции")
    description: str | None = PydField(default=None, description="Описание интеграции")
    endpoint: str | None = PydField(default=None, description="endpoint (для локальных интеграций)")
    webhooks: list[str] | None = PydField(default=None, description="Список подключённых вебхуков")
    image_url: str | None = PydField(default=None, description="URL изображения")
    docs_url: str | None = PydField(default=None, description="Ссылка на документацию по интеграции")
    version: str | None = PydField(default=None, description="Версия")
    has_web_ui: bool | None = PydField(default=None, description="Есть ли у интеграции веб-интерфейс")
    proxy_enabled: bool | None = PydField(default=None, description="Включён ли proxy-режим интеграции")
    web_ui_url: str | None = PydField(default=None, description="URL веб-интерфейса подключённой интеграции")
    has_iap: bool | None = PydField(default=None, description="Есть ли у интеграции in-app purchase")
    key: str | None = PydField(default=None, description="key (системное название) интеграции")
    is_public: bool | None = PydField(default=None, description="Флаг интеграция публичная или нет")
    connected_integration_id: str | None = PydField(default=None)
    alias: str | None = PydField(default=None, description="Alias подключённой интеграции")
    owner: IntegrationOwnerEnum | None = PydField(default=None, description="Владелец интеграции")
    handler: IntegrationHandlerEnum | None = PydField(default=None, description="Обработчки интеграции")
    handlers: list[IntegrationHandlerEnum] | None = PydField(default=None, description="Список поддерживаемых обработчиков интеграции")
    scheduled: bool | None = PydField(default=None, description="Флаг является ли интеграция планируемый")
    schedule: IntegrationSchedule | None = PydField(default=None, description="Модель расписания для интеграции")
    check_enabled: bool | None = PydField(default=None, description="Флаг поддерживает ли интеграция метод check")
    is_active: bool | None = PydField(default=None, description="Активна или нет")
    user: User | None = PydField(default=None, description="Пользователь, который подключил интеграцию")


class IntegrationConnectedGet(RegosModel):
    "Модель запроса подключённых интеграций"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    is_public: bool | None = PydField(default=None, description="Если true то интеграция тиражируемая. false - локальная")
    keys: list[str] | None = PydField(default=None, description="Массив ключей (системных названий) интеграций")
    connected_integration_ids: list[str] | None = PydField(default=None, description="Массив ID подключеных интеграций")
    include_schedule: bool | None = PydField(default=None, description="Заполняется ли расписание: true - Заполняется, false - Не заполняется")
    include_name: bool | None = PydField(default=None, description="Заполняется ли наименование и описание: true - Заполняется, false - Не заполняется")
    handler: IntegrationHandlerEnum | None = PydField(default=None, description="Фильтр по основному обработчику интеграции")
    handlers: list[IntegrationHandlerEnum] | None = PydField(default=None, description="Фильтр по поддерживаемым обработчикам интеграции. Не заменяет handler")
    user_id: int | None = PydField(default=None, description="ID пользователя, создавшего локальную интеграцию")


class IntegrationConnectedRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[IntegrationConnected] | Error | None = PydField(default=None, description="Массив результата.")


class IntegrationDisconnect(RegosModel):
    "Модель для отключения интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="Устаревшее поле. Будет удалено после 16.03.2027. Используется, если не передан connected_integration_id. Если по key\nнайдено более одной подключённой интеграции, метод вернёт ошибку 1100")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции. Имеет приоритет над key (если переданы оба поля)")


class IntegrationHandlerEnum(str, Enum):
    "Перечисление обработчиков интеграций"
    Default = "Default"
    MarketPlace = "MarketPlace"
    EPS = "EPS"
    EDO = "EDO"
    SMS = "SMS"
    TG_BOT = "TG_BOT"
    Custom = "Custom"
    Email = "Email"
    ChatBot = "ChatBot"
    Widget = "Widget"


class IntegrationLocalAdd(RegosModel):
    "Модель для добавления локальной интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Название интеграции")
    endpoint: str | None = PydField(default=None, description="Endpoint")
    webhooks: list[str] | None = PydField(default=None, description="Массив вебхуков")


class IntegrationLocalDelete(RegosModel):
    "Модель для удаления локальной интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ (системное название) интеграции")


class IntegrationLocalEdit(RegosModel):
    "Модель для редактирования локальной интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ (системное название) интеграции")
    name: str | None = PydField(default=None, description="Название интеграции")
    endpoint: str | None = PydField(default=None, description="Endpoint")
    webhooks: list[str] | None = PydField(default=None, description="Массив вебхуков")


class IntegrationOwnerEnum(str, Enum):
    "Перечисление владельцев интеграций"
    Default = "Default"
    Global = "Global"
    Firm = "Firm"


class IntegrationReconnect(RegosModel):
    "Модель для переподключения интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="Устаревшее поле. Будет удалено после 16.03.2027. Используется, если не передан connected_integration_id. Если по key\nнайдено более одной подключённой интеграции, метод вернёт ошибку 1100")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции. Имеет приоритет над key (если переданы оба поля)")


class IntegrationSchedule(RegosModel):
    "Модель расписания для интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scheduler_uuid: str | None = PydField(default=None, description="UUID расписания")
    period_type: IntegrationSchedulePeriodTypeEnum | None = PydField(default=None, description="Перечисление типов периодов для интеграции")
    period_value: int | None = PydField(default=None)
    last_execute: _DateTime | None = PydField(default=None)


class IntegrationSchedulePeriodTypeEnum(str, Enum):
    "Перечисление типов периодов для интеграции"
    Default = "Default"
    None_ = "None"
    Minute = "Minute"
    Hour = "Hour"
    Day = "Day"
    Week = "Week"
    Month = "Month"
    Year = "Year"


class IntegrationUnConnected(RegosModel):
    "Модель описывающая доступную интеграцию"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ (системное название) интеграции")
    is_public: bool | None = PydField(default=None, description="метка публичности интеграции")
    name: str | None = PydField(default=None, description="Название интеграции")
    description: str | None = PydField(default=None, description="Описание интеграции")
    scheduled: bool | None = PydField(default=None, description="Флаг является ли интеграция планируемый")
    check_enabled: bool | None = PydField(default=None, description="Флаг поддерживает ли интеграция метод check")
    handler: IntegrationHandlerEnum | None = PydField(default=None, description="Обработчки интеграции")
    handlers: list[IntegrationHandlerEnum] | None = PydField(default=None, description="Список поддерживаемых обработчиков интеграции")
    image_url: str | None = PydField(default=None, description="URL изображения")
    docs_url: str | None = PydField(default=None, description="Ссылка на документацию по интеграции")
    webhooks: list[str] | None = PydField(default=None, description="Список подключённых вебхуков")
    version: str | None = PydField(default=None, description="Версия")
    has_web_ui: bool | None = PydField(default=None, description="Есть ли у интеграции веб-интерфейс")
    proxy_enabled: bool | None = PydField(default=None, description="Включён ли proxy-режим интеграции")
    has_iap: bool | None = PydField(default=None, description="Есть ли у интеграции in-app purchase")


class IntegrationUnConnectedGet(RegosModel):
    "Модель запроса не подключённых интеграций (магазин интеграций)"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    keys: list[str] | None = PydField(default=None, description="массив ключей интеграций (необязательный)")
    group_ids: list[int] | None = PydField(default=None, description="массив  интеграций (необязательный)")
    handlers: list[IntegrationHandlerEnum] | None = PydField(default=None, description="массив поддерживаемых обработчиков интеграций (необязательный)")
    limit: int | None = PydField(default=None)
    offset: int | None = PydField(default=None)


class IntegrationUnConnectedRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[IntegrationUnConnected] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, SingleObjectResult
from schemas.api.rbac.user import User


IntegrationAddRequest: TypeAlias = IntegrationLocalAdd
IntegrationAddResponse: TypeAlias = SingleObjectResult
IntegrationConnectRequest: TypeAlias = IntegrationConnect
IntegrationConnectResponse: TypeAlias = SingleObjectResult
IntegrationDeleteRequest: TypeAlias = IntegrationLocalDelete
IntegrationDeleteResponse: TypeAlias = SingleObjectResult
IntegrationEditRequest: TypeAlias = IntegrationLocalEdit
IntegrationEditResponse: TypeAlias = SingleObjectResult
IntegrationGetRequest: TypeAlias = IntegrationUnConnectedGet
IntegrationGetResponse: TypeAlias = IntegrationUnConnectedRegosOffsettedArrayResult


_MODEL_NAMES = ['IntegrationConnect', 'IntegrationConnected', 'IntegrationConnectedGet', 'IntegrationConnectedRegosArrayResult', 'IntegrationDisconnect', 'IntegrationLocalAdd', 'IntegrationLocalDelete', 'IntegrationLocalEdit', 'IntegrationReconnect', 'IntegrationSchedule', 'IntegrationUnConnected', 'IntegrationUnConnectedGet', 'IntegrationUnConnectedRegosOffsettedArrayResult']


__all__ = [
    'IntegrationConnect',
    'IntegrationConnected',
    'IntegrationConnectedGet',
    'IntegrationConnectedRegosArrayResult',
    'IntegrationDisconnect',
    'IntegrationHandlerEnum',
    'IntegrationLocalAdd',
    'IntegrationLocalDelete',
    'IntegrationLocalEdit',
    'IntegrationOwnerEnum',
    'IntegrationReconnect',
    'IntegrationSchedule',
    'IntegrationSchedulePeriodTypeEnum',
    'IntegrationUnConnected',
    'IntegrationUnConnectedGet',
    'IntegrationUnConnectedRegosOffsettedArrayResult',
    'IntegrationGetRequest',
    'IntegrationGetResponse',
    'IntegrationConnectRequest',
    'IntegrationConnectResponse',
    'IntegrationAddRequest',
    'IntegrationAddResponse',
    'IntegrationEditRequest',
    'IntegrationEditResponse',
    'IntegrationDeleteRequest',
    'IntegrationDeleteResponse'
]
