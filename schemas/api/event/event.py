"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class EventGet(RegosModel):
    "Параметры получения сохранённых событий."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    connected_integration_id: str | None = PydField(default=None, description="Подключённая интеграция, для которой нужно восстановить события.")
    last_event_id: str | None = PydField(default=None, description="Последний полученный event_id. Возвращаются события после него.")
    from_date: int | None = PydField(default=None, description="Unix-время UTC, с которого нужно вернуть события.")
    limit: int | None = PydField(default=None, description="Максимальное количество событий в ответе.")
    actions: list[WebHookActionsEnum] | None = PydField(default=None, description="Фильтр по типам событий.")


class EventGetResult(RegosModel):
    "Результат получения сохранённых событий."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    events: list[EventItem] | None = PydField(default=None, description="События.")
    next_event_id: str | None = PydField(default=None, description="event_id последнего события в ответе.")
    has_more: bool | None = PydField(default=None, description="Признак наличия следующей страницы.")


class EventGetResultRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: EventGetResult | Error | None = PydField(default=None, description="Объект результата.")


class EventItem(RegosModel):
    "Сохранённое событие."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    event_id: str | None = PydField(default=None, description="Уникальный идентификатор события.")
    occurred_at: _DateTime | None = PydField(default=None, description="Дата и время возникновения события в UTC.")
    action: WebHookActionsEnum | None = PydField(default=None, description="Тип события.")
    data: Any = PydField(default=None, description="Полезная нагрузка события.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.webhooks.webhook import WebHookActionsEnum


EventGetRequest: TypeAlias = EventGet
EventGetResponse: TypeAlias = EventGetResultRegosObjectResult


_MODEL_NAMES = ['EventGet', 'EventGetResult', 'EventGetResultRegosObjectResult', 'EventItem']


__all__ = [
    'EventGet',
    'EventGetResult',
    'EventGetResultRegosObjectResult',
    'EventItem',
    'EventGetRequest',
    'EventGetResponse'
]
