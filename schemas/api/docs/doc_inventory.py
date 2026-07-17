"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocInventory(RegosModel):
    "Модель, описывающая документ инвентаризации"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа инвентаризации")
    code: str | None = PydField(default=None, description="Код документа")
    open_date: int | None = PydField(default=None, description="Дата открытия документа инвентаризации в формате unix time в секундах")
    close_date: int | None = PydField(default=None, description="Дата закрытия документа инвентаризации в формате unix time в секундах")
    compare_type: DocInventoryCompareType | None = PydField(default=None, description="Тип сопоставления: <open_date | 1> - На дату открытия, <close_date | 2> - На дату закрытия, <operation_date | 3> - На дату операции")
    stock: Stock | None = PydField(default=None, description="Склад")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    price_type: PriceType | None = PydField(default=None, description="Вид цены")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    closed: bool | None = PydField(default=None, description="Метка о закрытии документа")
    full: bool | None = PydField(default=None, description="Флаг показываеющий полная инвенторизация или нет")
    create_docinout: bool | None = PydField(default=None, description="Флаг показываеющий необходимость автоматического создания документов списания занесения при закрытии инвентаризации")
    external_id: str | None = PydField(default=None, description="ID документа во внешней системе")
    current_user_blocked: bool | None = PydField(default=None, description="Флаг показываеющий, что документ заблокирован текущим пользователем. Null если документ не блокирован")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class DocInventoryAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    open_date: int | None = PydField(default=None, description="Дата открытия инвентаризации в формате unix time в секундах")
    compare_type: DocInventoryCompareType | None = PydField(default=None, description="Тип сопоставления: <open_date | 1> - На дату открытия, <close_date | 2> - На дату закрытия, <operation_date | 3> - На дату операции")
    stock_id: int | None = PydField(default=None, description="ID склада")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    price_type_id: int | None = PydField(default=None, description="ID вида цены для занесения операци документа")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    full: bool | None = PydField(default=None, description="Флаг, показываеющий полная инвентаризация или нет. Полная - true, неполная - false. По умолчанию - true. Если true, то\nпри закрытии инвентаризаци (DocInventory/Close) в документ будут добавлены все позиции номенклатуры по складу документа,\nимеющие на данном складе не нулевые остатки. Добавление идёт по следующим правилам: фактическое количество будет 0,\nкол-во учёт - остаток на складе: если тип сопоставления open_date - то на дату открытия, иначе - на дату закрытия\nдокумента(close_date). При установленном значение поля full недоступно вручную добавить всю номенклатуру в документ")
    create_docinout: bool | None = PydField(default=None, description="Флаг показываеющий необходимость автоматического создания документов списания/занесения на основании документа\nинвентаризации при закрытии инвентаризации: true - создавать, false - не создавать. По умолчанию true. При\ncreate_docinout = true при закрытии документа инвентаризации (DocInventory/Close) будут созданы документы\nсписания/занесения на основании документа инвентаризации; созданный документ списания/занесения не будут связаны с\nдокументом инвентаризации и при открытии и повторном закрытии документа инвентаризации будут созданы новый документ\nсписания/занесения")
    external_id: str | None = PydField(default=None, description="ID документа во внешней системе")


class DocInventoryCloseAndOpen(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа инвентаризации")


class DocInventoryColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocInventoryColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocInventoryColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Code = "Code"
    OpenDate = "OpenDate"
    CloseDate = "CloseDate"
    CompareType = "CompareType"
    StockName = "StockName"
    AttacheUserName = "AttacheUserName"
    Blocked = "Blocked"
    Closed = "Closed"
    DeletedMark = "DeletedMark"
    LastUpdate = "LastUpdate"


class DocInventoryCompareType(str, Enum):
    open_date = "open_date"
    close_date = "close_date"
    operation_date = "operation_date"


class DocInventoryDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа инвентаризации")


class DocInventoryDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа инвентаризации")


class DocInventoryEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа инвентаризации")
    open_date: int | None = PydField(default=None, description="Дата открытия инвентаризации в формате unix time в секундах")
    compare_type: DocInventoryCompareType | None = PydField(default=None, description="Тип сопоставления: <open_date | 1> - На дату открытия, <close_date | 2> - На дату закрытия, <operation_date | 3> - На дату операции")
    stock_id: int | None = PydField(default=None, description="ID склада")
    price_type_id: int | None = PydField(default=None, description="ID вида цены для занесения операци документа. Цена в существующих операциях не пересчитывается при изменении вида цены документа")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    full: bool | None = PydField(default=None, description="Флаг, показываеющий полная инвентаризация или нет. Полная - true, неполная - false. По умолчанию - true. Если true, то\nпри закрытии инвентаризаци (DocInventory/Close) в документ будут добавлены все позиции номенклатуры по складу документа,\nимеющие на данном складе не нулевые остатки. Добавление идёт по следующим правилам: фактическое количество будет 0,\nкол-во учёт - остаток на складе: если тип сопоставления open_date - то на дату открытия, иначе - на дату закрытия\nдокумента(close_date). При установленном значение поля full недоступно вручную добавить всю номенклатуру в документ")
    create_docinout: bool | None = PydField(default=None, description="Флаг показываеющий необходимость автоматического создания документов списания/занесения на основании документа\nинвентаризации при закрытии инвентаризации: true - создавать, false - не создавать. По умолчанию true. При\ncreate_docinout = true при закрытии документа инвентаризации (DocInventory/Close) будут созданы документы\nсписания/занесения на основании документа инвентаризации; созданный документ списания/занесения не будут связаны с\nдокументом инвентаризации и при открытии и повторном закрытии документа инвентаризации будут созданы новый документ\nсписания/занесения")
    external_id: str | None = PydField(default=None, description="ID документа во внешней системе")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


class DocInventoryGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    compare_type: DocInventoryCompareType | None = PydField(default=None, description="Тип сопоставления: <open_date | 1> - На дату открытия, <close_date | 2> - На дату закрытия, <operation_date | 3> - На дату операции")
    ids: list[int] | None = PydField(default=None, description="Массив id документов перемещения")
    stock_ids: list[int] | None = PydField(default=None, description="Массив id складов")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив id ответственных пользователей")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    closed: bool | None = PydField(default=None, description="Закрыт ли документ: true - закрыт, false - не закрыт")
    blocked: bool | None = PydField(default=None, description="Заблокирован ли документ: true - заблокирован, false - не заблокирован")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    search: str | None = PydField(default=None, description="Поиск по значениям полей: code, firm->name, firm->inn, stock_name, attached_user_name")
    sort_orders: list[DocInventoryColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocInventoryLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив Id документов инвентаризации")


class DocInventoryRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocInventory] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.references.price_type import PriceType
from schemas.api.references.stock import Stock


DocInventoryAddRequest: TypeAlias = DocInventoryAdd
DocInventoryAddResponse: TypeAlias = InsertResult
DocInventoryCloseRequest: TypeAlias = DocInventoryCloseAndOpen
DocInventoryCloseResponse: TypeAlias = UpdateResult
DocInventoryDeleteMarkRequest: TypeAlias = DocInventoryDeleteMark
DocInventoryDeleteMarkResponse: TypeAlias = UpdateResult
DocInventoryDeleteRequest: TypeAlias = DocInventoryDelete
DocInventoryDeleteResponse: TypeAlias = UpdateResult
DocInventoryEditRequest: TypeAlias = DocInventoryEdit
DocInventoryEditResponse: TypeAlias = UpdateResult
DocInventoryGetRequest: TypeAlias = DocInventoryGet
DocInventoryGetResponse: TypeAlias = DocInventoryRegosOffsettedArrayResult
DocInventoryLockRequest: TypeAlias = DocInventoryLockAndUnlock
DocInventoryLockResponse: TypeAlias = UpdateResult
DocInventoryOpenRequest: TypeAlias = DocInventoryCloseAndOpen
DocInventoryOpenResponse: TypeAlias = UpdateResult
DocInventoryUnlockRequest: TypeAlias = DocInventoryLockAndUnlock
DocInventoryUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocInventory', 'DocInventoryAdd', 'DocInventoryCloseAndOpen', 'DocInventoryColumn', 'DocInventoryDelete', 'DocInventoryDeleteMark', 'DocInventoryEdit', 'DocInventoryGet', 'DocInventoryLockAndUnlock', 'DocInventoryRegosOffsettedArrayResult']


__all__ = [
    'DocInventory',
    'DocInventoryAdd',
    'DocInventoryCloseAndOpen',
    'DocInventoryColumn',
    'DocInventoryColumns',
    'DocInventoryCompareType',
    'DocInventoryDelete',
    'DocInventoryDeleteMark',
    'DocInventoryEdit',
    'DocInventoryGet',
    'DocInventoryLockAndUnlock',
    'DocInventoryRegosOffsettedArrayResult',
    'DocInventoryGetRequest',
    'DocInventoryGetResponse',
    'DocInventoryAddRequest',
    'DocInventoryAddResponse',
    'DocInventoryEditRequest',
    'DocInventoryEditResponse',
    'DocInventoryDeleteMarkRequest',
    'DocInventoryDeleteMarkResponse',
    'DocInventoryDeleteRequest',
    'DocInventoryDeleteResponse',
    'DocInventoryLockRequest',
    'DocInventoryLockResponse',
    'DocInventoryUnlockRequest',
    'DocInventoryUnlockResponse',
    'DocInventoryCloseRequest',
    'DocInventoryCloseResponse',
    'DocInventoryOpenRequest',
    'DocInventoryOpenResponse'
]
