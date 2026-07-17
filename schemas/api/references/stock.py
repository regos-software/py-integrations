"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Stock(RegosModel):
    "Модель, описывающая склады"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID склада")
    name: str | None = PydField(default=None, description="Наименование склада")
    address: str | None = PydField(default=None, description="Адрес склада")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    area: _Decimal | None = PydField(default=None, description="Площадь")
    description: str | None = PydField(default=None, description="Примечание")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class StockAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование склада")
    firm_id: int | None = PydField(default=None, description="Id фирмы, к которой принадлежит склад")
    address: str | None = PydField(default=None, description="Адрес склада")
    area: _Decimal | None = PydField(default=None, description="Площадь. Если поле задано, то его значение должно быть > 0")
    description: str | None = PydField(default=None, description="Примечание")


class StockDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id склада")


class StockDeleteConfirm(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    confirm_code: str | None = PydField(default=None, description="Код подтверждения удаления склада")
    id: int | None = PydField(default=None, description="Id склада")


class StockDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id склада")


class StockEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id склада")
    name: str | None = PydField(default=None, description="Наименование склада")
    address: str | None = PydField(default=None, description="Адрес склада")
    area: _Decimal | None = PydField(default=None, description="Площадь. Если поле задано, то его значение должно быть > 0")
    description: str | None = PydField(default=None, description="Примечание")


class StockGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    sort_orders: list[Stock_SortOrder] | None = PydField(default=None, description="Сортировка выходных данных")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class StockRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Stock] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class Stock_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: Stock_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class Stock_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ApiResult, ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.references.firm import Firm


StockAddRequest: TypeAlias = StockAdd
StockAddResponse: TypeAlias = InsertResult
StockDeleteConfirmRequest: TypeAlias = StockDeleteConfirm
StockDeleteConfirmResponse: TypeAlias = ApiResult
StockDeleteMarkRequest: TypeAlias = StockDeleteMark
StockDeleteMarkResponse: TypeAlias = UpdateResult
StockDeleteRequest: TypeAlias = StockDelete
StockDeleteResponse: TypeAlias = ApiResult
StockEditRequest: TypeAlias = StockEdit
StockEditResponse: TypeAlias = UpdateResult
StockGetRequest: TypeAlias = StockGet
StockGetResponse: TypeAlias = StockRegosOffsettedArrayResult


_MODEL_NAMES = ['Stock', 'StockAdd', 'StockDelete', 'StockDeleteConfirm', 'StockDeleteMark', 'StockEdit', 'StockGet', 'StockRegosOffsettedArrayResult', 'Stock_SortOrder']


__all__ = [
    'Stock',
    'StockAdd',
    'StockDelete',
    'StockDeleteConfirm',
    'StockDeleteMark',
    'StockEdit',
    'StockGet',
    'StockRegosOffsettedArrayResult',
    'Stock_SortOrder',
    'Stock_SortOrderColumn',
    'StockGetRequest',
    'StockGetResponse',
    'StockAddRequest',
    'StockAddResponse',
    'StockEditRequest',
    'StockEditResponse',
    'StockDeleteMarkRequest',
    'StockDeleteMarkResponse',
    'StockDeleteRequest',
    'StockDeleteResponse',
    'StockDeleteConfirmRequest',
    'StockDeleteConfirmResponse'
]
