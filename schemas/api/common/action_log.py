"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ActionType(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    name: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class Actionlog(RegosModel):
    "Модель описывающая лог действий"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id лога")
    user: User | None = PydField(default=None, description="Пользователь")
    table: Table | None = PydField(default=None, description="Таблица, в которой произведены изменения")
    action_type: ActionType | None = PydField(default=None, description="Тип действия")
    record_id: int | None = PydField(default=None, description="Id записи, к которой были произведены действия")
    record_name: str | None = PydField(default=None, description="Наименование записи, к которой были произведены действия")
    description: str | None = PydField(default=None, description="Описание")
    date: int | None = PydField(default=None, description="Дата действия в формате Unix time в секундах")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class ActionlogGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_ids: list[int] | None = PydField(default=None, description="Массив id пользователей")
    table_ids: list[int] | None = PydField(default=None, description="Массив id таблиц")
    record_id: int | None = PydField(default=None, description="ID записи, к которой было применено изменение")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class ActionlogRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Actionlog] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, Table
from schemas.api.rbac.user import User


ActionLogGetRequest: TypeAlias = ActionlogGet
ActionLogGetResponse: TypeAlias = ActionlogRegosOffsettedArrayResult


_MODEL_NAMES = ['ActionType', 'Actionlog', 'ActionlogGet', 'ActionlogRegosOffsettedArrayResult']


__all__ = [
    'ActionType',
    'Actionlog',
    'ActionlogGet',
    'ActionlogRegosOffsettedArrayResult',
    'ActionLogGetRequest',
    'ActionLogGetResponse'
]
