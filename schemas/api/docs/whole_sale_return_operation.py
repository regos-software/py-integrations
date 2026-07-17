"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class WholeSaleReturnOperation(RegosModel):
    "Модель, описывающая операции возврата от контрагента"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа возврата от контрагента")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    order: int | None = PydField(default=None, description="Порядок операции")
    price: _Decimal | None = PydField(default=None, description="Цена со скидкой")
    price2: _Decimal | None = PydField(default=None, description="Цена без скидки")
    last_purchase_cost: _Decimal | None = PydField(default=None, description="Стоимость последней закупки")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки Ндс")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    description: str | None = PydField(default=None, description="Примечание")
    last_update: int | None = PydField(default=None, description="Время последнего изменения в формате unix time в секундах")


class WholeSaleReturnOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции (NULL = не задано, в БД сохраняется как NULL).\nДля версий БД ниже 363 игнорируется.")
    price: _Decimal | None = PydField(default=None)
    price2: _Decimal | None = PydField(default=None)
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class WholeSaleReturnOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class WholeSaleReturnOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции. Если NULL, значение в БД не меняется.\nДля версий БД ниже 363 игнорируется.")
    price: _Decimal | None = PydField(default=None)
    price2: _Decimal | None = PydField(default=None)
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class WholeSaleReturnOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций возврата от контрагентов")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номентклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class WholeSaleReturnOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[WholeSaleReturnOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DiscountOperationAdd, DiscountOperationDelete, DiscountOperationGet, DiscountOperationRegosArrayResult, DocsOperationsMovement, Error, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


WholeSaleReturnOperationAddDiscountRequest: TypeAlias = DiscountOperationAdd
WholeSaleReturnOperationAddDiscountResponse: TypeAlias = UpdateResult
WholeSaleReturnOperationAddRequest: TypeAlias = list[WholeSaleReturnOperationAdd]
WholeSaleReturnOperationAddResponse: TypeAlias = UpdateResult
WholeSaleReturnOperationDeleteDiscountRequest: TypeAlias = DiscountOperationDelete
WholeSaleReturnOperationDeleteDiscountResponse: TypeAlias = UpdateResult
WholeSaleReturnOperationDeleteRequest: TypeAlias = list[WholeSaleReturnOperationDelete]
WholeSaleReturnOperationDeleteResponse: TypeAlias = UpdateResult
WholeSaleReturnOperationEditRequest: TypeAlias = list[WholeSaleReturnOperationEdit]
WholeSaleReturnOperationEditResponse: TypeAlias = UpdateResult
WholeSaleReturnOperationGetDiscountRequest: TypeAlias = DiscountOperationGet
WholeSaleReturnOperationGetDiscountResponse: TypeAlias = DiscountOperationRegosArrayResult
WholeSaleReturnOperationGetRequest: TypeAlias = WholeSaleReturnOperationGet
WholeSaleReturnOperationGetResponse: TypeAlias = WholeSaleReturnOperationRegosOffsettedArrayResult
WholeSaleReturnOperationMoveOprerationsRequest: TypeAlias = DocsOperationsMovement
WholeSaleReturnOperationMoveOprerationsResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['WholeSaleReturnOperation', 'WholeSaleReturnOperationAdd', 'WholeSaleReturnOperationDelete', 'WholeSaleReturnOperationEdit', 'WholeSaleReturnOperationGet', 'WholeSaleReturnOperationRegosOffsettedArrayResult']


__all__ = [
    'WholeSaleReturnOperation',
    'WholeSaleReturnOperationAdd',
    'WholeSaleReturnOperationDelete',
    'WholeSaleReturnOperationEdit',
    'WholeSaleReturnOperationGet',
    'WholeSaleReturnOperationRegosOffsettedArrayResult',
    'WholeSaleReturnOperationGetRequest',
    'WholeSaleReturnOperationGetResponse',
    'WholeSaleReturnOperationAddRequest',
    'WholeSaleReturnOperationAddResponse',
    'WholeSaleReturnOperationEditRequest',
    'WholeSaleReturnOperationEditResponse',
    'WholeSaleReturnOperationDeleteRequest',
    'WholeSaleReturnOperationDeleteResponse',
    'WholeSaleReturnOperationGetDiscountRequest',
    'WholeSaleReturnOperationGetDiscountResponse',
    'WholeSaleReturnOperationAddDiscountRequest',
    'WholeSaleReturnOperationAddDiscountResponse',
    'WholeSaleReturnOperationDeleteDiscountRequest',
    'WholeSaleReturnOperationDeleteDiscountResponse',
    'WholeSaleReturnOperationMoveOprerationsRequest',
    'WholeSaleReturnOperationMoveOprerationsResponse'
]
