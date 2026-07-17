"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ProjectTask(RegosModel):
    "Модель, описывающая задачу проекта"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID задачи")
    project_id: int | None = PydField(default=None, description="ID проекта")
    parent_task_id: int | None = PydField(default=None, description="ID родительской задачи (null для задачи верхнего уровня)")
    name: str | None = PydField(default=None, description="Наименование задачи")
    description: str | None = PydField(default=None, description="Описание задачи")
    description_mentions: list[CommonMention] | None = PydField(default=None, description="Упоминания пользователей в description, возвращаются при include_mentions = true")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    deal_id: int | None = PydField(default=None, description="Идентификатор связанной CRM-сделки.")
    client: Client | None = PydField(default=None, description="Вложенная модель CRM-клиента")
    chat_id: str | None = PydField(default=None, description="UUID чата задачи (обсуждение и системные события)")
    observer_user_ids: list[int] | None = PydField(default=None, description="IDs наблюдателей задачи")
    status: ProjectTaskStatusEnum | None = PydField(default=None, description="Статус задачи: New, InProgress, Done, Canceled")
    due_date: int | None = PydField(default=None, description="Срок выполнения (Unix time, сек.)")
    created_date: int | None = PydField(default=None, description="Дата создания задачи (Unix time, сек.)")
    attachment_file_ids: list[int] | None = PydField(default=None, description="IDs файлов-вложений")
    inline_file_ids: list[int] | None = PydField(default=None, description="IDs встроенных файлов")
    fields: list[FieldValue] | None = PydField(default=None, description="Дополнительные поля")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего задачу")
    closed_user_id: int | None = PydField(default=None, description="ID пользователя, закрывшего задачу")
    closed_date: int | None = PydField(default=None, description="Дата закрытия (Unix time, сек.)")
    deleted: bool | None = PydField(default=None, description="Признак удаления")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")


class ProjectTaskAdd(RegosModel):
    "Входная модель создания задачи."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    project_id: int | None = PydField(default=None, description="ID проекта")
    parent_task_id: int | None = PydField(default=None, description="ID родительской задачи (создание подзадачи)")
    name: str | None = PydField(default=None, description="Наименование задачи")
    description: str | None = PydField(default=None, description="Описание задачи")
    description_mentions: list[CommonMentionInput] | None = PydField(default=None, description="Структурированные упоминания пользователей в description")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    responsible_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    client_id: int | None = PydField(default=None, description="ID CRM-клиента для привязки к задаче")
    deal_id: int | None = PydField(default=None, description="ID CRM-сделки для привязки к задаче")
    observer_user_ids: list[int] | None = PydField(default=None, description="IDs наблюдателей")
    due_date: int | None = PydField(default=None, description="Срок выполнения (Unix time, сек.)")
    attachment_file_ids: list[int] | None = PydField(default=None, description="IDs файлов-вложений")
    inline_file_ids: list[int] | None = PydField(default=None, description="IDs встроенных файлов")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Массив значений дополнительных полей")


class ProjectTaskDelete(RegosModel):
    "Входная модель удаления задачи."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID задачи")


class ProjectTaskEdit(RegosModel):
    "Входная модель редактирования задачи."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID задачи")
    parent_task_id: int | None = PydField(default=None, description="Новый ID родительской задачи (должен ссылаться на существующую задачу)")
    name: str | None = PydField(default=None, description="Новое наименование задачи")
    description: str | None = PydField(default=None, description="Новое описание задачи")
    description_mentions: list[CommonMentionInput] | None = PydField(default=None, description="Новый список структурированных упоминаний в description")
    mention_options: CommonMentionOptions | None = PydField(default=None, description="Опции обработки упоминаний")
    client_id: int | None = PydField(default=None, description="Новый ID CRM-клиента (0 — снять текущую привязку)")
    deal_id: int | None = PydField(default=None, description="Новый ID CRM-сделки (0 — снять текущую привязку)")
    attachment_file_ids: list[int] | None = PydField(default=None, description="Обновленный список файлов-вложений")
    inline_file_ids: list[int] | None = PydField(default=None, description="Обновленный список встроенных файлов")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Массив значений дополнительных полей")


class ProjectTaskGet(RegosModel):
    "Входная модель фильтрации задач."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID задач")
    project_ids: list[int] | None = PydField(default=None, description="Массив ID проектов")
    parent_task_ids: list[int] | None = PydField(default=None, description="Фильтр по ID родительских задач")
    responsible_user_ids: list[int] | None = PydField(default=None, description="Фильтр по ответственным")
    client_ids: list[int] | None = PydField(default=None, description="Фильтр по связанным CRM-клиентам")
    deal_ids: list[int] | None = PydField(default=None, description="Фильтр по связанным CRM-сделкам")
    observer_user_ids: list[int] | None = PydField(default=None, description="Фильтр по наблюдателям")
    statuses: list[ProjectTaskStatusEnum] | None = PydField(default=None, description="Фильтр по статусам (New, InProgress, Done, Canceled)")
    due_from: int | None = PydField(default=None, description="Начало периода срока выполнения (Unix time, сек.)")
    due_to: int | None = PydField(default=None, description="Конец периода срока выполнения (Unix time, сек.)")
    filters: list[Filter] | None = PydField(default=None, description="Дополнительные условия фильтрации")
    search: str | None = PydField(default=None, description="Поиск по полям name и description")
    include_mentions: bool | None = PydField(default=None, description="Вернуть description_mentions для описания задачи")
    limit: int | None = PydField(default=None, description="Лимит элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")
    sort_orders: list[BaseSortColumn] | None = PydField(default=None, description="Сортировка результата")


class ProjectTaskRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ProjectTask] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ProjectTaskSetDue(RegosModel):
    "Входная модель изменения срока выполнения задачи."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID задачи")
    due_date: int | None = PydField(default=None, description="Новый срок выполнения (Unix time, сек.). 0 или null — снять срок")


class ProjectTaskSetObservers(RegosModel):
    "Входная модель изменения наблюдателей задачи."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID задачи")
    observer_user_ids: list[int] | None = PydField(default=None, description="Список ID наблюдателей")
    replace_mode: bool | None = PydField(default=None, description="true — заменить список, false — добавить к текущему")


class ProjectTaskSetProject(RegosModel):
    "Входная модель переноса задачи в другой проект."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID задачи")
    project_id: int | None = PydField(default=None, description="ID целевого проекта")


class ProjectTaskSetResponsible(RegosModel):
    "Входная модель смены ответственного по задаче."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID задачи")
    responsible_user_id: int | None = PydField(default=None, description="ID нового ответственного")


class ProjectTaskSetStatus(RegosModel):
    "Входная модель изменения статуса задачи."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID задачи")
    status: ProjectTaskStatusEnum | None = PydField(default=None, description="Новый статус: New, InProgress, Done, Canceled")


class ProjectTaskStatusEnum(str, Enum):
    "Статус задачи проекта."
    Default = "Default"
    New = "New"
    InProgress = "InProgress"
    Done = "Done"
    Canceled = "Canceled"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BaseSortColumn, CommonMention, CommonMentionInput, CommonMentionOptions, Error, InsertResult, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.crm.client import Client
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit


ProjectTaskAddRequest: TypeAlias = ProjectTaskAdd
ProjectTaskAddResponse: TypeAlias = InsertResult
ProjectTaskDeleteRequest: TypeAlias = ProjectTaskDelete
ProjectTaskDeleteResponse: TypeAlias = UpdateResult
ProjectTaskEditRequest: TypeAlias = ProjectTaskEdit
ProjectTaskEditResponse: TypeAlias = UpdateResult
ProjectTaskGetRequest: TypeAlias = ProjectTaskGet
ProjectTaskGetResponse: TypeAlias = ProjectTaskRegosOffsettedArrayResult
ProjectTaskSetDueRequest: TypeAlias = ProjectTaskSetDue
ProjectTaskSetDueResponse: TypeAlias = UpdateResult
ProjectTaskSetObserversRequest: TypeAlias = ProjectTaskSetObservers
ProjectTaskSetObserversResponse: TypeAlias = UpdateResult
ProjectTaskSetProjectRequest: TypeAlias = ProjectTaskSetProject
ProjectTaskSetProjectResponse: TypeAlias = UpdateResult
ProjectTaskSetResponsibleRequest: TypeAlias = ProjectTaskSetResponsible
ProjectTaskSetResponsibleResponse: TypeAlias = UpdateResult
ProjectTaskSetStatusRequest: TypeAlias = ProjectTaskSetStatus
ProjectTaskSetStatusResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['ProjectTask', 'ProjectTaskAdd', 'ProjectTaskDelete', 'ProjectTaskEdit', 'ProjectTaskGet', 'ProjectTaskRegosOffsettedArrayResult', 'ProjectTaskSetDue', 'ProjectTaskSetObservers', 'ProjectTaskSetProject', 'ProjectTaskSetResponsible', 'ProjectTaskSetStatus']


__all__ = [
    'ProjectTask',
    'ProjectTaskAdd',
    'ProjectTaskDelete',
    'ProjectTaskEdit',
    'ProjectTaskGet',
    'ProjectTaskRegosOffsettedArrayResult',
    'ProjectTaskSetDue',
    'ProjectTaskSetObservers',
    'ProjectTaskSetProject',
    'ProjectTaskSetResponsible',
    'ProjectTaskSetStatus',
    'ProjectTaskStatusEnum',
    'ProjectTaskGetRequest',
    'ProjectTaskGetResponse',
    'ProjectTaskAddRequest',
    'ProjectTaskAddResponse',
    'ProjectTaskEditRequest',
    'ProjectTaskEditResponse',
    'ProjectTaskDeleteRequest',
    'ProjectTaskDeleteResponse',
    'ProjectTaskSetStatusRequest',
    'ProjectTaskSetStatusResponse',
    'ProjectTaskSetDueRequest',
    'ProjectTaskSetDueResponse',
    'ProjectTaskSetProjectRequest',
    'ProjectTaskSetProjectResponse',
    'ProjectTaskSetResponsibleRequest',
    'ProjectTaskSetResponsibleResponse',
    'ProjectTaskSetObserversRequest',
    'ProjectTaskSetObserversResponse'
]
