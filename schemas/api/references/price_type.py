"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PriceType(RegosModel):
    "Модель, описывающая виды цен"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id вида цены")
    name: str | None = PydField(default=None, description="Наименование вида цены")
    round_to: _Decimal | None = PydField(default=None, description="Предел округления")
    markup: _Decimal | None = PydField(default=None, description="Наценка для вида цены")
    max_discount: _Decimal | None = PydField(default=None, description="Максимальная скидка")
    currency: Currency | None = PydField(default=None, description="Валюта")
    currency_additional: Currency | None = PydField(default=None, description="Дополнительная валюта")
    last_update: int | None = PydField(default=None, description="Последнее изменение строки в формате unix time в секундах")


class PriceTypeAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование вида цены")
    currency_id: int | None = PydField(default=None, description="id валюты")
    currency_additional_id: int | None = PydField(default=None, description="id дополнительной валюты")
    round_to: _Decimal | None = PydField(default=None, description="Предел округления")
    markup: _Decimal | None = PydField(default=None, description="Наценка для вида цены")
    max_discount: _Decimal | None = PydField(default=None, description="Максимальная скидка")


class PriceTypeDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id вида цены")


class PriceTypeEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id вида цены")
    currency_id: int | None = PydField(default=None, description="id валюты")
    currency_additional_id: int | None = PydField(default=None, description="id дополнительной валюты")
    name: str | None = PydField(default=None, description="Наименование вида цены")
    round_to: _Decimal | None = PydField(default=None, description="Предел округления")
    markup: _Decimal | None = PydField(default=None, description="Наценка для вида цены")
    max_discount: _Decimal | None = PydField(default=None, description="Максимальная скидка")


class PriceTypeGet(RegosModel):
    "модель для получения списка вида цены"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив Id видов цен")
    currency_ids: list[int] | None = PydField(default=None, description="ID валюты")
    sort_orders: list[PriceType_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по: name (наименование вида цены)")
    limit: int | None = PydField(default=None, description="Количество элементов выборки, возвращаемых при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class PriceTypeRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PriceType] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class PriceType_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: PriceType_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class PriceType_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    RoundTo = "RoundTo"
    MarkUp = "MarkUp"
    MaxDiscount = "MaxDiscount"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.references.currency import Currency


PriceTypeAddRequest: TypeAlias = PriceTypeAdd
PriceTypeAddResponse: TypeAlias = InsertResult
PriceTypeDeleteRequest: TypeAlias = PriceTypeDelete
PriceTypeDeleteResponse: TypeAlias = UpdateResult
PriceTypeEditRequest: TypeAlias = PriceTypeEdit
PriceTypeEditResponse: TypeAlias = UpdateResult
PriceTypeGetRequest: TypeAlias = PriceTypeGet
PriceTypeGetResponse: TypeAlias = PriceTypeRegosOffsettedArrayResult


_MODEL_NAMES = ['PriceType', 'PriceTypeAdd', 'PriceTypeDelete', 'PriceTypeEdit', 'PriceTypeGet', 'PriceTypeRegosOffsettedArrayResult', 'PriceType_SortOrder']


__all__ = [
    'PriceType',
    'PriceTypeAdd',
    'PriceTypeDelete',
    'PriceTypeEdit',
    'PriceTypeGet',
    'PriceTypeRegosOffsettedArrayResult',
    'PriceType_SortOrder',
    'PriceType_SortOrderColumn',
    'PriceTypeGetRequest',
    'PriceTypeGetResponse',
    'PriceTypeAddRequest',
    'PriceTypeAddResponse',
    'PriceTypeEditRequest',
    'PriceTypeEditResponse',
    'PriceTypeDeleteRequest',
    'PriceTypeDeleteResponse'
]
