"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Deal(RegosModel):
    "Модели Deal"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID сделки")
    client_id: int | None = PydField(default=None, description="ID клиента")
    client: Client | None = PydField(default=None, description="Вложенный объект клиента")
    task_id: int | None = PydField(default=None, description="ID связанной задачи проекта.")
    lead_id: int | None = PydField(default=None, description="ID исходного обращения (если сделка создана из Lead)")
    ticket_id: int | None = PydField(default=None, description="ID тикета-источника (информационная ссылка)")
    source_deal_id: int | None = PydField(default=None, description="ID исходной сделки (информационная ссылка)")
    deal_type_id: int | None = PydField(default=None, description="Тип сделки")
    pipeline_id: int | None = PydField(default=None, description="Воронка сделки")
    stage_id: int | None = PydField(default=None, description="Текущая стадия")
    title: str | None = PydField(default=None, description="Наименование сделки")
    description: str | None = PydField(default=None, description="Описание сделки")
    description_mentions: list[CommonMention] | None = PydField(default=None, description="Упоминания пользователей в description, возвращаются при include_mentions = true")
    amount: _Decimal | None = PydField(default=None, description="Сумма сделки")
    currency: Currency | None = PydField(default=None, description="Валюта сделки")
    responsible_user_id: int | None = PydField(default=None, description="Ответственный сотрудник")
    participant_user_ids: list[int] | None = PydField(default=None, description="Участники-сотрудники сделки")
    open_date: int | None = PydField(default=None, description="Дата открытия (Unix time, сек.)")
    close_date: int | None = PydField(default=None, description="Дата закрытия (Unix time, сек.)")
    fields: list[FieldValue] | None = PydField(default=None, description="Значения дополнительных полей")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего запись")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")
    chat_id: str | None = PydField(default=None, description="UUID связанного чата сделки")


class DealAdd(RegosModel):
    "Модель создания сделки."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    source_lead_id: int | None = PydField(default=None, description="ID исходного лида (информационная ссылка)")
    ticket_id: int | None = PydField(default=None, description="ID исходного тикета (информационная ссылка)")
    source_deal_id: int | None = PydField(default=None, description="ID исходной сделки (информационная ссылка)")
    client_id: int | None = PydField(default=None, description="ID клиента в CRM")
    task_id: int | None = PydField(default=None, description="ID связанной задачи проекта")
    chat_id: str | None = PydField(default=None, description="UUID существующего чата, который нужно привязать к сделке (task-chat использовать нельзя)")
    lead_id: int | None = PydField(default=None, description="ID исходного обращения")
    deal_type_id: int | None = PydField(default=None, description="ID типа сделки")
    pipeline_id: int | None = PydField(default=None, description="ID воронки; если не передан, используется воронка по умолчанию для Deal")
    stage_id: int | None = PydField(default=None, description="ID не терминальной стадии; если не передан, используется стартовая стадия воронки")
    title: str | None = PydField(default=None, description="Название сделки")
    description: str | None = PydField(default=None, description="Описание сделки")
    description_mentions: list[CommonMentionInput] | None = PydField(default=None, description="Структурированные упоминания пользователей в description")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    amount: _Decimal | None = PydField(default=None, description="Сумма сделки")
    currency_id: int | None = PydField(default=None, description="ID валюты (ctlg_common_currency_ref.crnc_id)")
    responsible_user_id: int | None = PydField(default=None, description="Ответственный пользователь")
    participant_user_ids: list[int] | None = PydField(default=None, description="Участники сделки")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Значения дополнительных полей")


class DealClose(RegosModel):
    "Модель закрытия сделки."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID сделки")
    stage_id: int | None = PydField(default=None, description="ID терминальной стадии воронки сделки")


class DealDelete(RegosModel):
    "Модель удаления сделки."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID сделки")


class DealEdit(RegosModel):
    "Модель редактирования сделки."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID сделки")
    task_id: int | None = PydField(default=None, description="ID связанной задачи проекта (0 — снять привязку)")
    deal_type_id: int | None = PydField(default=None, description="ID типа сделки")
    pipeline_id: int | None = PydField(default=None, description="Изменение воронки через edit запрещено; используйте отдельный сценарий смены стадии/воронки")
    stage_id: int | None = PydField(default=None, description="Изменение стадии через edit запрещено; используйте deal/setstage")
    title: str | None = PydField(default=None, description="Название сделки")
    description: str | None = PydField(default=None, description="Описание сделки")
    description_mentions: list[CommonMentionInput] | None = PydField(default=None, description="Новый список структурированных упоминаний в description")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    amount: _Decimal | None = PydField(default=None, description="Сумма сделки")
    currency_id: int | None = PydField(default=None, description="ID валюты (ctlg_common_currency_ref.crnc_id)")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Изменения дополнительных полей")


class DealGet(RegosModel):
    "Модель фильтров и пагинации для получения списка сделок."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID сделок")
    client_ids: list[int] | None = PydField(default=None, description="Фильтр по связанным клиентам")
    task_ids: list[int] | None = PydField(default=None, description="Фильтр по связанным задачам проекта")
    lead_ids: list[int] | None = PydField(default=None, description="Фильтр по связанным обращениям")
    responsible_user_ids: list[int] | None = PydField(default=None, description="Фильтр по ответственным")
    stage_ids: list[int] | None = PydField(default=None, description="Фильтр по стадиям")
    pipeline_id: int | None = PydField(default=None, description="Фильтр по воронке")
    currency_id: int | None = PydField(default=None, description="Фильтр по валюте сделки")
    from_date: int | None = PydField(default=None, description="Нижняя граница open_date (дата старта сделки, Unix time, сек.)")
    to_date: int | None = PydField(default=None, description="Верхняя граница open_date (дата старта сделки, Unix time, сек.)")
    include_mentions: bool | None = PydField(default=None, description="Вернуть description_mentions для описания сделки")
    filters: list[Filter] | None = PydField(default=None, description="Дополнительные фильтры по основным и пользовательским полям")
    limit: int | None = PydField(default=None, description="Лимит выборки, при <= 0 используется 100, максимум 1000")
    offset: int | None = PydField(default=None, description="Смещение выборки, при < 0 используется 0")


class DealRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Deal] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DealSetParticipants(RegosModel):
    "Модель управления участниками сделки."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID сделки")
    participant_user_ids: list[int] | None = PydField(default=None, description="Список участников")
    replace_mode: bool | None = PydField(default=None, description="Режим обновления: true — заменить состав, false — добавить к текущему")


class DealSetResponsible(RegosModel):
    "Модель назначения ответственного по сделке."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID сделки")
    responsible_user_id: int | None = PydField(default=None, description="ID нового ответственного")


class DealSetStage(RegosModel):
    "Модель смены стадии сделки."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID сделки")
    stage_id: int | None = PydField(default=None, description="ID новой стадии")
    comment: str | None = PydField(default=None, description="Комментарий к смене стадии")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import CommonMention, CommonMentionInput, CommonMentionOptions, Error, InsertResult, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.crm.client import Client
from schemas.api.references.currency import Currency
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit


DealAddRequest: TypeAlias = DealAdd
DealAddResponse: TypeAlias = InsertResult
DealCloseRequest: TypeAlias = DealClose
DealCloseResponse: TypeAlias = UpdateResult
DealDeleteRequest: TypeAlias = DealDelete
DealDeleteResponse: TypeAlias = UpdateResult
DealEditRequest: TypeAlias = DealEdit
DealEditResponse: TypeAlias = UpdateResult
DealGetRequest: TypeAlias = DealGet
DealGetResponse: TypeAlias = DealRegosOffsettedArrayResult
DealSetParticipantsRequest: TypeAlias = DealSetParticipants
DealSetParticipantsResponse: TypeAlias = UpdateResult
DealSetResponsibleRequest: TypeAlias = DealSetResponsible
DealSetResponsibleResponse: TypeAlias = UpdateResult
DealSetStageRequest: TypeAlias = DealSetStage
DealSetStageResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Deal', 'DealAdd', 'DealClose', 'DealDelete', 'DealEdit', 'DealGet', 'DealRegosOffsettedArrayResult', 'DealSetParticipants', 'DealSetResponsible', 'DealSetStage']


__all__ = [
    'Deal',
    'DealAdd',
    'DealClose',
    'DealDelete',
    'DealEdit',
    'DealGet',
    'DealRegosOffsettedArrayResult',
    'DealSetParticipants',
    'DealSetResponsible',
    'DealSetStage',
    'DealGetRequest',
    'DealGetResponse',
    'DealAddRequest',
    'DealAddResponse',
    'DealEditRequest',
    'DealEditResponse',
    'DealSetStageRequest',
    'DealSetStageResponse',
    'DealSetResponsibleRequest',
    'DealSetResponsibleResponse',
    'DealSetParticipantsRequest',
    'DealSetParticipantsResponse',
    'DealCloseRequest',
    'DealCloseResponse',
    'DealDeleteRequest',
    'DealDeleteResponse'
]
