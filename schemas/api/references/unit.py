"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Unit(RegosModel):
    "Модель, описывающая единицы измерения"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id единицы измерения")
    name: str | None = PydField(default=None, description="Наименование единицы измерения")
    type: UnitType | None = PydField(default=None, description="Тип единицы измерения: <non_pcs | 1> - Нештучная, <pcs | 2> Штучная")
    description: str | None = PydField(default=None, description="Описание единицы измерения")
    kkm_code: int | None = PydField(default=None, description="Устаревшее поле. Значение по умолчанию: 1. Поле устарело и будет удалено после 10.03.2027")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class UnitAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование единицы измерения")
    type: UnitType | None = PydField(default=None, description="Тип единицы измерения: <non_pcs | 1> (не штучный (весовой)), <pcs | 2> (штучный)")
    kkm_code: int | None = PydField(default=None, description="Устаревший код единицы измерения для совместимости со старыми ККМ-интеграциями")
    description: str | None = PydField(default=None, description="Описание единицы измерения")


class UnitDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id единицы измерения")


class UnitEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id единицы измерения")
    name: str | None = PydField(default=None, description="Наименование единицы измерения")
    type: UnitType | None = PydField(default=None, description="Тип единицы измерения: <non_pcs | 1> (не штучный (весовой)), <pcs | 2> (штучный)")
    kkm_code: int | None = PydField(default=None, description="Устаревший код единицы измерения для совместимости со старыми ККМ-интеграциями")
    description: str | None = PydField(default=None, description="Описание единицы измерения")


class UnitGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id единиц измерения")
    type: UnitType | None = PydField(default=None, description="Тип единицы измерения: <non_pcs | 1> (не штучный (весовой)), <pcs | 2> (штучный)")
    sort_orders: list[UnitSortOrder] | None = PydField(default=None, description="Сортировка выходных данных")
    search: str | None = PydField(default=None, description="Строка поиска по полю: name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class UnitRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Unit] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class UnitSortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: UnitSortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class UnitSortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    Type = "Type"
    LastUpdate = "LastUpdate"


class UnitType(str, Enum):
    Default = "Default"
    non_pcs = "non_pcs"
    pcs = "pcs"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


UnitAddRequest: TypeAlias = UnitAdd
UnitAddResponse: TypeAlias = InsertResult
UnitDeleteRequest: TypeAlias = UnitDelete
UnitDeleteResponse: TypeAlias = UpdateResult
UnitEditRequest: TypeAlias = UnitEdit
UnitEditResponse: TypeAlias = UpdateResult
UnitGetRequest: TypeAlias = UnitGet
UnitGetResponse: TypeAlias = UnitRegosOffsettedArrayResult


_MODEL_NAMES = ['Unit', 'UnitAdd', 'UnitDelete', 'UnitEdit', 'UnitGet', 'UnitRegosOffsettedArrayResult', 'UnitSortOrder']


__all__ = [
    'Unit',
    'UnitAdd',
    'UnitDelete',
    'UnitEdit',
    'UnitGet',
    'UnitRegosOffsettedArrayResult',
    'UnitSortOrder',
    'UnitSortOrderColumn',
    'UnitType',
    'UnitGetRequest',
    'UnitGetResponse',
    'UnitAddRequest',
    'UnitAddResponse',
    'UnitEditRequest',
    'UnitEditResponse',
    'UnitDeleteRequest',
    'UnitDeleteResponse'
]
