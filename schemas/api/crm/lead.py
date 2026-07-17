"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Lead(RegosModel):
    "Модели Lead"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID обращения")
    client_id: int | None = PydField(default=None, description="ID клиента")
    client: Client | None = PydField(default=None, description="Вложенный объект клиента")
    pipeline_id: int | None = PydField(default=None, description="ID воронки")
    stage_id: int | None = PydField(default=None, description="ID текущей стадии")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного сотрудника")
    participant_user_ids: list[int] | None = PydField(default=None, description="IDs участников-сотрудников обращения")
    title: str | None = PydField(default=None, description="Тема обращения")
    description: str | None = PydField(default=None, description="Описание обращения")
    description_mentions: list[CommonMention] | None = PydField(default=None, description="Упоминания пользователей в description, возвращаются при include_mentions = true")
    amount: _Decimal | None = PydField(default=None, description="Сумма обращения")
    start_date: int | None = PydField(default=None, description="Дата начала обработки (Unix time, сек.)")
    end_date: int | None = PydField(default=None, description="Дата завершения обработки (Unix time, сек.)")
    converted_deal_id: int | None = PydField(default=None, description="ID сделки, созданной из обращения")
    repeat_of_lead_id: int | None = PydField(default=None, description="ID исходного обращения, если это повтор")
    ticket_id: int | None = PydField(default=None, description="ID тикета-источника (информационная ссылка)")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего запись")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")
    chat_id: str | None = PydField(default=None, description="UUID связанного чата обращения")
    fields: list[FieldValue] | None = PydField(default=None, description="Значения дополнительных полей")


class LeadAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    client_id: int | None = PydField(default=None, description="ID клиента в CRM")
    ticket_id: int | None = PydField(default=None, description="ID тикета-источника (информационная ссылка)")
    chat_id: str | None = PydField(default=None, description="UUID существующего чата, который нужно привязать к лиду")
    pipeline_id: int | None = PydField(default=None, description="ID воронки; если не передан, используется воронка по умолчанию для Lead")
    stage_id: int | None = PydField(default=None, description="ID не терминальной стадии; если не передан, используется стартовая стадия воронки")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    participant_user_ids: list[int] | None = PydField(default=None, description="Участники обращения")
    title: str | None = PydField(default=None, description="Тема обращения")
    description: str | None = PydField(default=None, description="Описание обращения")
    description_mentions: list[CommonMentionInput] | None = PydField(default=None, description="Структурированные упоминания пользователей в description")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    amount: _Decimal | None = PydField(default=None, description="Сумма обращения")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Значения дополнительных полей")


class LeadClose(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID обращения")
    stage_id: int | None = PydField(default=None, description="Терминальная неуспешная стадия (is_terminal = true, is_success = false)")


class LeadConvert(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID обращения")
    target_entity_type: CrmEntityTypeEnum | None = PydField(default=None, description="Целевая сущность, допустимо только Deal")
    deal_type_id: int | None = PydField(default=None, description="ID типа сделки")
    deal_title: str | None = PydField(default=None, description="Название создаваемой сделки")
    pipeline_id: int | None = PydField(default=None, description="Воронка сделки")
    stage_id: int | None = PydField(default=None, description="Стадия сделки")
    responsible_user_id: int | None = PydField(default=None, description="Ответственный по сделке")
    participant_user_ids: list[int] | None = PydField(default=None, description="Участники сделки")
    amount: _Decimal | None = PydField(default=None, description="Сумма сделки; если не передана, используется lead.amount (если задана у лида)")
    currency_id: int | None = PydField(default=None, description="ID валюты (ctlg_common_currency_ref.crnc_id)")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Дополнительные поля сделки")


class LeadDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID обращения")


class LeadEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID обращения")
    stage_id: int | None = PydField(default=None, description="Изменение стадии через edit запрещено; используйте lead/setstage")
    title: str | None = PydField(default=None, description="Тема обращения")
    description: str | None = PydField(default=None, description="Описание обращения")
    description_mentions: list[CommonMentionInput] | None = PydField(default=None, description="Новый список структурированных упоминаний в description")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    amount: _Decimal | None = PydField(default=None, description="Сумма обращения")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Изменения дополнительных полей")


class LeadGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID обращений")
    client_ids: list[int] | None = PydField(default=None, description="Фильтр по связанным клиентам")
    search: str | None = PydField(default=None, description="Поиск по полям обращения (title, description)")
    responsible_user_ids: list[int] | None = PydField(default=None, description="Фильтр по ответственным")
    stage_ids: list[int] | None = PydField(default=None, description="Фильтр по стадиям")
    from_date: int | None = PydField(default=None, description="Нижняя граница start_date (Unix time, сек.)")
    to_date: int | None = PydField(default=None, description="Верхняя граница start_date (Unix time, сек.)")
    include_mentions: bool | None = PydField(default=None, description="Вернуть description_mentions для описания обращения")
    filters: list[Filter] | None = PydField(default=None, description="Дополнительные фильтры по основным и пользовательским полям")
    limit: int | None = PydField(default=None, description="Лимит выборки, при <= 0 используется 100, максимум 1000")
    offset: int | None = PydField(default=None, description="Смещение выборки, при < 0 используется 0")


class LeadRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Lead] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class LeadSetParticipants(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID обращения")
    participant_user_ids: list[int] | None = PydField(default=None, description="Список участников")
    replace_mode: bool | None = PydField(default=None, description="Режим обновления: true — заменить состав, false — добавить к текущему")


class LeadSetResponsible(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID обращения")
    responsible_user_id: int | None = PydField(default=None, description="ID нового ответственного")


class LeadSetStage(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID обращения")
    stage_id: int | None = PydField(default=None, description="ID новой стадии")
    comment: str | None = PydField(default=None, description="Комментарий к смене стадии")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import CommonMention, CommonMentionInput, CommonMentionOptions, CrmEntityTypeEnum, Error, InsertResult, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.crm.client import Client
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit


LeadAddRequest: TypeAlias = LeadAdd
LeadAddResponse: TypeAlias = InsertResult
LeadCloseRequest: TypeAlias = LeadClose
LeadCloseResponse: TypeAlias = UpdateResult
LeadConvertRequest: TypeAlias = LeadConvert
LeadConvertResponse: TypeAlias = InsertResult
LeadDeleteRequest: TypeAlias = LeadDelete
LeadDeleteResponse: TypeAlias = UpdateResult
LeadEditRequest: TypeAlias = LeadEdit
LeadEditResponse: TypeAlias = UpdateResult
LeadGetRequest: TypeAlias = LeadGet
LeadGetResponse: TypeAlias = LeadRegosOffsettedArrayResult
LeadSetParticipantsRequest: TypeAlias = LeadSetParticipants
LeadSetParticipantsResponse: TypeAlias = UpdateResult
LeadSetResponsibleRequest: TypeAlias = LeadSetResponsible
LeadSetResponsibleResponse: TypeAlias = UpdateResult
LeadSetStageRequest: TypeAlias = LeadSetStage
LeadSetStageResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Lead', 'LeadAdd', 'LeadClose', 'LeadConvert', 'LeadDelete', 'LeadEdit', 'LeadGet', 'LeadRegosOffsettedArrayResult', 'LeadSetParticipants', 'LeadSetResponsible', 'LeadSetStage']


__all__ = [
    'Lead',
    'LeadAdd',
    'LeadClose',
    'LeadConvert',
    'LeadDelete',
    'LeadEdit',
    'LeadGet',
    'LeadRegosOffsettedArrayResult',
    'LeadSetParticipants',
    'LeadSetResponsible',
    'LeadSetStage',
    'LeadGetRequest',
    'LeadGetResponse',
    'LeadAddRequest',
    'LeadAddResponse',
    'LeadEditRequest',
    'LeadEditResponse',
    'LeadSetStageRequest',
    'LeadSetStageResponse',
    'LeadSetResponsibleRequest',
    'LeadSetResponsibleResponse',
    'LeadSetParticipantsRequest',
    'LeadSetParticipantsResponse',
    'LeadCloseRequest',
    'LeadCloseResponse',
    'LeadDeleteRequest',
    'LeadDeleteResponse',
    'LeadConvertRequest',
    'LeadConvertResponse'
]
