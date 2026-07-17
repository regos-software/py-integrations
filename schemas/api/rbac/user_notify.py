"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class NotifyEntityEnum(str, Enum):
    Default = "Default"
    DocOrderDelivery = "DocOrderDelivery"
    Report = "Report"
    Campaign = "Campaign"
    IntegrationLocal = "IntegrationLocal"
    IntegrationPublic = "IntegrationPublic"
    User = "User"
    Project = "Project"
    ProjectTask = "ProjectTask"
    Chat = "Chat"
    Crm = "Crm"
    Lead = "Lead"
    Deal = "Deal"
    Storage = "Storage"
    Mention = "Mention"


class UserNotify(RegosModel):
    "Модель, описывающая уведомления пользователя"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    entity: NotifyEntityEnum | None = PydField(default=None, description="Сущность")
    notification_key: str | None = PydField(default=None, description="Код шаблона (ключ уведомления)")
    value: bool | None = PydField(default=None, description="Подключено (true) / отключено (false)")


class UserNotifyGet(RegosModel):
    "модель для получения уведомлений пользователя"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя в системе")


class UserNotifyRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[UserNotify] | Error | None = PydField(default=None, description="Массив результата.")


class UserNotifySet(RegosModel):
    "модель для установки подписки уведомления"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя")
    notification_key: str | None = PydField(default=None, description="Код шаблона (ключ уведомления)")
    value: bool | None = PydField(default=None, description="Значение (true/false)")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, UpdateResult


UserNotifyGetRequest: TypeAlias = UserNotifyGet
UserNotifyGetResponse: TypeAlias = UserNotifyRegosArrayResult
UserNotifySetRequest: TypeAlias = list[UserNotifySet]
UserNotifySetResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['UserNotify', 'UserNotifyGet', 'UserNotifyRegosArrayResult', 'UserNotifySet']


__all__ = [
    'NotifyEntityEnum',
    'UserNotify',
    'UserNotifyGet',
    'UserNotifyRegosArrayResult',
    'UserNotifySet',
    'UserNotifyGetRequest',
    'UserNotifyGetResponse',
    'UserNotifySetRequest',
    'UserNotifySetResponse'
]
