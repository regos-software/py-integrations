"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Ticket(RegosModel):
    "Модели Ticket"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID тикета")
    client_id: int | None = PydField(default=None, description="ID клиента")
    client: Client | None = PydField(default=None, description="Вложенный объект клиента")
    channel_id: int | None = PydField(default=None, description="ID канала")
    direction: TicketDirectionEnum | None = PydField(default=None, description="Направление (Inbound, Outbound)")
    external_dialog_id: str | None = PydField(default=None, description="Внешний ID диалога")
    subject: str | None = PydField(default=None, description="Тема обращения")
    description: str | None = PydField(default=None, description="Описание обращения")
    description_mentions: list[CommonMention] | None = PydField(default=None, description="Упоминания пользователей в description, возвращаются при include_mentions = true")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного")
    participant_user_ids: list[int] | None = PydField(default=None, description="Участники-сотрудники тикета")
    status: TicketStatusEnum | None = PydField(default=None, description="Статус тикета (Open, Closed, WaitingClient, WaitingStaff)")
    first_response_date: int | None = PydField(default=None, description="Дата первого ответа")
    first_response_due_date: int | None = PydField(default=None, description="SLA-срок первого ответа")
    resolve_due_date: int | None = PydField(default=None, description="SLA-срок решения")
    sla_breached: bool | None = PydField(default=None, description="Признак нарушения SLA")
    sla_breached_date: int | None = PydField(default=None, description="Дата нарушения SLA")
    resolved_date: int | None = PydField(default=None, description="Дата закрытия")
    missed: bool | None = PydField(default=None, description="Признак пропущенного обращения")
    rating: int | None = PydField(default=None, description="Оценка")
    rating_comment: str | None = PydField(default=None, description="Комментарий к оценке")
    client_sentiment_score: int | None = PydField(default=None, description="Оценка настроения клиента ответственным оператором")
    client_sentiment_comment: str | None = PydField(default=None, description="Комментарий к оценке настроения клиента")
    client_sentiment_user_id: int | None = PydField(default=None, description="ID пользователя, установившего оценку настроения клиента")
    client_sentiment_date: int | None = PydField(default=None, description="Дата установки оценки настроения клиента (Unix time, сек.)")
    chat_id: str | None = PydField(default=None, description="UUID чата тикета")
    fields: list[FieldValue] | None = PydField(default=None, description="Значения дополнительных полей")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего запись")
    created_date: int | None = PydField(default=None, description="Дата создания (Unix time, сек.)")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")


class TicketAdd(RegosModel):
    "Параметры создания тикета."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    client_id: int | None = PydField(default=None, description="ID клиента")
    channel_id: int | None = PydField(default=None, description="ID канала")
    direction: TicketDirectionEnum | None = PydField(default=None, description="Направление (Inbound, Outbound), по умолчанию Inbound")
    external_dialog_id: str | None = PydField(default=None, description="Внешний ID диалога")
    subject: str | None = PydField(default=None, description="Тема обращения")
    description: str | None = PydField(default=None, description="Описание обращения")
    description_mentions: list[CommonMentionInput] | None = PydField(default=None, description="Структурированные упоминания пользователей в description")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    participant_user_ids: list[int] | None = PydField(default=None, description="Участники тикета (сотрудники)")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Значения дополнительных полей")


class TicketClose(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID тикета")
    resolved_date: int | None = PydField(default=None, description="Дата закрытия (Unix time, сек.), если не передана — используется текущее время")


class TicketDelete(RegosModel):
    "Параметры удаления тикета."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID тикета")


class TicketDirectionEnum(str, Enum):
    Default = "Default"
    Inbound = "Inbound"
    Outbound = "Outbound"


class TicketEdit(RegosModel):
    "Параметры редактирования тикета."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID тикета")
    direction: TicketDirectionEnum | None = PydField(default=None, description="Направление (Inbound, Outbound)")
    subject: str | None = PydField(default=None, description="Тема обращения")
    description: str | None = PydField(default=None, description="Описание обращения")
    description_mentions: list[CommonMentionInput] | None = PydField(default=None, description="Новый список структурированных упоминаний в description")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Изменение дополнительных полей")


class TicketGet(RegosModel):
    "Параметры запроса списка тикетов."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID тикетов")
    search: str | None = PydField(default=None, description="Поиск по subject тикета и данным клиента (name, phone)")
    client_ids: list[int] | None = PydField(default=None, description="Фильтр по клиентам")
    channel_ids: list[int] | None = PydField(default=None, description="Фильтр по каналам")
    external_dialog_id: str | None = PydField(default=None, description="Фильтр по внешнему ID диалога")
    responsible_user_ids: list[int] | None = PydField(default=None, description="Фильтр по ответственным")
    statuses: list[TicketStatusEnum] | None = PydField(default=None, description="Фильтр по статусу (Open, Closed, WaitingClient, WaitingStaff)")
    direction: TicketDirectionEnum | None = PydField(default=None, description="Фильтр по направлению (Inbound, Outbound)")
    from_date: int | None = PydField(default=None, description="Нижняя граница created_date")
    to_date: int | None = PydField(default=None, description="Верхняя граница created_date")
    include_mentions: bool | None = PydField(default=None, description="Вернуть description_mentions для описания тикета")
    filters: list[Filter] | None = PydField(default=None, description="Дополнительные фильтры")
    sort_orders: list[TicketSortColumn] | None = PydField(default=None, description="DESC\" }]")
    limit: int | None = PydField(default=None, description="Лимит записей.")
    offset: int | None = PydField(default=None, description="Смещение выборки.")


class TicketRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Ticket] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class TicketSetClientSentiment(RegosModel):
    "Параметры установки операторской оценки настроения клиента по тикету."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID тикета")
    sentiment_score: int | None = PydField(default=None, description="Оценка настроения клиента в диапазоне 1..5")
    sentiment_comment: str | None = PydField(default=None, description="Комментарий к оценке настроения клиента")


class TicketSetParticipants(RegosModel):
    "Параметры закрытия тикета."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID тикета")
    participant_user_ids: list[int] | None = PydField(default=None, description="Список участников")
    replace_mode: bool | None = PydField(default=None, description="Режим обновления: true — заменить состав, false — добавить к текущему")


class TicketSetRating(RegosModel):
    "Параметры установки оценки по тикету."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID тикета")
    rating: int | None = PydField(default=None, description="Оценка в диапазоне 1..5")
    rating_comment: str | None = PydField(default=None, description="Комментарий к оценке")


class TicketSetResponsible(RegosModel):
    "Параметры назначения ответственного по тикету."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID тикета")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


class TicketSetStatus(RegosModel):
    "Параметры изменения статуса тикета."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID тикета")
    status: TicketStatusEnum | None = PydField(default=None, description="Новый статус (Open, Closed, WaitingClient, WaitingStaff)")


class TicketSortColumn(RegosModel):
    "Элемент сортировки для Ticket.Get."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: TicketSortOrderColumnsEnum | None = PydField(default=None, description="Поле сортировки.")
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="Направление сортировки.")


class TicketSortOrderColumnsEnum(str, Enum):
    "Доступные поля сортировки для Ticket.Get."
    default = "default"
    id = "id"
    created_date = "created_date"
    last_update = "last_update"
    status = "status"
    direction = "direction"
    resolved_date = "resolved_date"
    sla_breached = "sla_breached"
    sla_breached_date = "sla_breached_date"
    first_response_date = "first_response_date"
    first_response_due_date = "first_response_due_date"
    resolve_due_date = "resolve_due_date"
    rating = "rating"
    channel_id = "channel_id"
    responsible_user_id = "responsible_user_id"
    client_name = "client.name"
    client_phone = "client.phone"
    client_sentiment_score = "client_sentiment_score"
    client_sentiment_date = "client_sentiment_date"
    client_sentiment_user_id = "client_sentiment_user_id"


class TicketStatusEnum(str, Enum):
    Default = "Default"
    Open = "Open"
    Closed = "Closed"
    WaitingClient = "WaitingClient"
    WaitingStaff = "WaitingStaff"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, CommonMention, CommonMentionInput, CommonMentionOptions, Error, InsertResult, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.crm.client import Client
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit


TicketAddRequest: TypeAlias = TicketAdd
TicketAddResponse: TypeAlias = InsertResult
TicketCloseRequest: TypeAlias = TicketClose
TicketCloseResponse: TypeAlias = UpdateResult
TicketDeleteRequest: TypeAlias = TicketDelete
TicketDeleteResponse: TypeAlias = UpdateResult
TicketEditRequest: TypeAlias = TicketEdit
TicketEditResponse: TypeAlias = UpdateResult
TicketGetRequest: TypeAlias = TicketGet
TicketGetResponse: TypeAlias = TicketRegosOffsettedArrayResult
TicketSetClientSentimentRequest: TypeAlias = TicketSetClientSentiment
TicketSetClientSentimentResponse: TypeAlias = UpdateResult
TicketSetParticipantsRequest: TypeAlias = TicketSetParticipants
TicketSetParticipantsResponse: TypeAlias = UpdateResult
TicketSetRatingRequest: TypeAlias = TicketSetRating
TicketSetRatingResponse: TypeAlias = UpdateResult
TicketSetResponsibleRequest: TypeAlias = TicketSetResponsible
TicketSetResponsibleResponse: TypeAlias = UpdateResult
TicketSetStatusRequest: TypeAlias = TicketSetStatus
TicketSetStatusResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Ticket', 'TicketAdd', 'TicketClose', 'TicketDelete', 'TicketEdit', 'TicketGet', 'TicketRegosOffsettedArrayResult', 'TicketSetClientSentiment', 'TicketSetParticipants', 'TicketSetRating', 'TicketSetResponsible', 'TicketSetStatus', 'TicketSortColumn']


__all__ = [
    'Ticket',
    'TicketAdd',
    'TicketClose',
    'TicketDelete',
    'TicketDirectionEnum',
    'TicketEdit',
    'TicketGet',
    'TicketRegosOffsettedArrayResult',
    'TicketSetClientSentiment',
    'TicketSetParticipants',
    'TicketSetRating',
    'TicketSetResponsible',
    'TicketSetStatus',
    'TicketSortColumn',
    'TicketSortOrderColumnsEnum',
    'TicketStatusEnum',
    'TicketGetRequest',
    'TicketGetResponse',
    'TicketAddRequest',
    'TicketAddResponse',
    'TicketEditRequest',
    'TicketEditResponse',
    'TicketSetResponsibleRequest',
    'TicketSetResponsibleResponse',
    'TicketSetParticipantsRequest',
    'TicketSetParticipantsResponse',
    'TicketSetStatusRequest',
    'TicketSetStatusResponse',
    'TicketSetRatingRequest',
    'TicketSetRatingResponse',
    'TicketSetClientSentimentRequest',
    'TicketSetClientSentimentResponse',
    'TicketCloseRequest',
    'TicketCloseResponse',
    'TicketDeleteRequest',
    'TicketDeleteResponse'
]
