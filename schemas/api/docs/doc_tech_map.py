"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocTechMap(RegosModel):
    "Модель, описывающая документ технологической карты"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа технологической карты")
    date: int | None = PydField(default=None, description="Дата документа технологической карты")
    type: DocTechMapType | None = PydField(default=None, description="Тип технологической карты: <Assemblable | 1> - Сборка, <Disassemblable | 2> - Разборка")
    code: str | None = PydField(default=None, description="Код документа технологической карты")
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    item: Item | None = PydField(default=None, description="Номенклатурва")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    performed: bool | None = PydField(default=None, description="Статус проведения документа технологической карты: true - Проведён, false - Не проведён")
    blocked: bool | None = PydField(default=None, description="Статус блокировки документа технологической карты для редактирования: true - Заблокирован для редактирования, false - Разблокирован для редактирования")
    current_user_blocked: bool | None = PydField(default=None, description="Статус блокировки документа технологической карты текущим пользователем: true - Заблокирован для редактирования текущим\nпользователем, false - Не заблокирован для редактирования текущим пользователем")
    autocalculate_part_cost: bool | None = PydField(default=None, description="Статус автоматического расчёта доли стоимости в операциях: true - Проценты в операциях будут рассчитаны автоматичесики,\nfalse - Проценты в операциях не будут рассчитаны автоматически")
    last_update: int | None = PydField(default=None, description="Время последнего изменения в формате Unix time")


class DocTechMapAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    type: DocTechMapType | None = PydField(default=None, description="Тип технической карты: <Assemblable | 1> - Сборка, <Disassemblable | 2> - Разборка")
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    autocalculate_part_cost: bool | None = PydField(default=None, description="Статус автоматического расчёта доли стоимости в операциях: true - Проценты в операциях будут рассчитаны автоматичесики,\nfalse - Проценты в операциях не будут рассчитаны автоматически")


class DocTechMapColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocTechMapColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocTechMapColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Date = "Date"
    Type = "Type"
    Code = "Code"
    ItemName = "ItemName"
    Performed = "Performed"
    Blocked = "Blocked"
    LastUpdate = "LastUpdate"


class DocTechMapEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа технической карты")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    autocalculate_part_cost: bool | None = PydField(default=None, description="Статус автоматического расчёта доли стоимости в операциях: true - Проценты в операциях будут рассчитаны автоматичесики,\nfalse - Проценты в операциях не будут рассчитаны автоматически")


class DocTechMapGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов технологических карт")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    type: DocTechMapType | None = PydField(default=None, description="Тип технологической карты: <Assemblable | 1> - Сборка, <Disassemblable | 2> - Разборка")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    performed: bool | None = PydField(default=None, description="Статус проведения документа технологической карты: true - Проведён, false - Не проведён")
    blocked: bool | None = PydField(default=None, description="Статус блокировки документа технологической карты для редактирования: true - Заблокирован для редактирования, false - Разблокирован для редактирования")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа технологической карты, Firm/name - Наименование предприятия,\nItem/name - Наименование номенклатуры, User/name - ФИО ответственного лица")
    sort_orders: list[DocTechMapColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocTechMapId(RegosModel):
    "модель для Delete, Perform, UnPerform, Lock, Unlock"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Массив ID документа технической карты")


class DocTechMapRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocTechMap] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocTechMapType(str, Enum):
    Default = "Default"
    Assemblable = "Assemblable"
    Disassemblable = "Disassemblable"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.references.firm import Firm
from schemas.api.references.item import Item


DocTechMapAddRequest: TypeAlias = DocTechMapAdd
DocTechMapAddResponse: TypeAlias = InsertResult
DocTechMapDeleteRequest: TypeAlias = DocTechMapId
DocTechMapDeleteResponse: TypeAlias = UpdateResult
DocTechMapEditRequest: TypeAlias = DocTechMapEdit
DocTechMapEditResponse: TypeAlias = UpdateResult
DocTechMapGetRequest: TypeAlias = DocTechMapGet
DocTechMapGetResponse: TypeAlias = DocTechMapRegosOffsettedArrayResult
DocTechMapLockRequest: TypeAlias = DocTechMapId
DocTechMapLockResponse: TypeAlias = UpdateResult
DocTechMapPerformCancelRequest: TypeAlias = DocTechMapId
DocTechMapPerformCancelResponse: TypeAlias = UpdateResult
DocTechMapPerformRequest: TypeAlias = DocTechMapId
DocTechMapPerformResponse: TypeAlias = UpdateResult
DocTechMapUnlockRequest: TypeAlias = DocTechMapId
DocTechMapUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocTechMap', 'DocTechMapAdd', 'DocTechMapColumn', 'DocTechMapEdit', 'DocTechMapGet', 'DocTechMapId', 'DocTechMapRegosOffsettedArrayResult']


__all__ = [
    'DocTechMap',
    'DocTechMapAdd',
    'DocTechMapColumn',
    'DocTechMapColumns',
    'DocTechMapEdit',
    'DocTechMapGet',
    'DocTechMapId',
    'DocTechMapRegosOffsettedArrayResult',
    'DocTechMapType',
    'DocTechMapGetRequest',
    'DocTechMapGetResponse',
    'DocTechMapAddRequest',
    'DocTechMapAddResponse',
    'DocTechMapEditRequest',
    'DocTechMapEditResponse',
    'DocTechMapDeleteRequest',
    'DocTechMapDeleteResponse',
    'DocTechMapLockRequest',
    'DocTechMapLockResponse',
    'DocTechMapUnlockRequest',
    'DocTechMapUnlockResponse',
    'DocTechMapPerformRequest',
    'DocTechMapPerformResponse',
    'DocTechMapPerformCancelRequest',
    'DocTechMapPerformCancelResponse'
]
