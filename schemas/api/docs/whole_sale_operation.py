"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class WholeSaleOperation(RegosModel):
    "Модель, описывающая операции документа отгрузки конрагенту"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа отгрузки конрагенту")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    order: int | None = PydField(default=None, description="Порядок операции")
    price: _Decimal | None = PydField(default=None, description="цена со скидкой")
    price2: _Decimal | None = PydField(default=None, description="цена без скидки")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки ндс")
    last_purchase_cost: _Decimal | None = PydField(default=None, description="Стоимость последней закупки")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    description: str | None = PydField(default=None, description="Примечание")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class WholeSaleOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции (NULL = не задано, в БД сохраняется как NULL).\nДля версий БД ниже 363 игнорируется.")
    price: _Decimal | None = PydField(default=None)
    price2: _Decimal | None = PydField(default=None)
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class WholeSaleOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class WholeSaleOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции. Если NULL, значение в БД не меняется.\nДля версий БД ниже 363 игнорируется.")
    price: _Decimal | None = PydField(default=None)
    price2: _Decimal | None = PydField(default=None)
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class WholeSaleOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="массив id операций документа")
    item_ids: list[int] | None = PydField(default=None, description="массив id номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class WholeSaleOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[WholeSaleOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DiscountOperationAdd, DiscountOperationDelete, DiscountOperationGet, DiscountOperationRegosArrayResult, DocsOperationsCopy, DocsOperationsMovement, Error, SetPriceByPriceType_Model, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


WholeSaleOperationAddDiscountRequest: TypeAlias = DiscountOperationAdd
WholeSaleOperationAddDiscountResponse: TypeAlias = UpdateResult
WholeSaleOperationAddRequest: TypeAlias = list[WholeSaleOperationAdd]
WholeSaleOperationAddResponse: TypeAlias = UpdateResult
WholeSaleOperationCopyOperationsFromDocOrderFromPartnerRequest: TypeAlias = DocsOperationsCopy
WholeSaleOperationCopyOperationsFromDocOrderFromPartnerResponse: TypeAlias = UpdateResult
WholeSaleOperationCopyOperationsFromDocPurchaseRequest: TypeAlias = DocsOperationsCopy
WholeSaleOperationCopyOperationsFromDocPurchaseResponse: TypeAlias = UpdateResult
WholeSaleOperationDeleteDiscountRequest: TypeAlias = DiscountOperationDelete
WholeSaleOperationDeleteDiscountResponse: TypeAlias = UpdateResult
WholeSaleOperationDeleteRequest: TypeAlias = list[WholeSaleOperationDelete]
WholeSaleOperationDeleteResponse: TypeAlias = UpdateResult
WholeSaleOperationEditRequest: TypeAlias = list[WholeSaleOperationEdit]
WholeSaleOperationEditResponse: TypeAlias = UpdateResult
WholeSaleOperationGetDiscountRequest: TypeAlias = DiscountOperationGet
WholeSaleOperationGetDiscountResponse: TypeAlias = DiscountOperationRegosArrayResult
WholeSaleOperationGetRequest: TypeAlias = WholeSaleOperationGet
WholeSaleOperationGetResponse: TypeAlias = WholeSaleOperationRegosOffsettedArrayResult
WholeSaleOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
WholeSaleOperationMoveOperationsResponse: TypeAlias = UpdateResult
WholeSaleOperationSetPriceByPriceTypeRequest: TypeAlias = SetPriceByPriceType_Model
WholeSaleOperationSetPriceByPriceTypeResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['WholeSaleOperation', 'WholeSaleOperationAdd', 'WholeSaleOperationDelete', 'WholeSaleOperationEdit', 'WholeSaleOperationGet', 'WholeSaleOperationRegosOffsettedArrayResult']


__all__ = [
    'WholeSaleOperation',
    'WholeSaleOperationAdd',
    'WholeSaleOperationDelete',
    'WholeSaleOperationEdit',
    'WholeSaleOperationGet',
    'WholeSaleOperationRegosOffsettedArrayResult',
    'WholeSaleOperationGetRequest',
    'WholeSaleOperationGetResponse',
    'WholeSaleOperationAddRequest',
    'WholeSaleOperationAddResponse',
    'WholeSaleOperationEditRequest',
    'WholeSaleOperationEditResponse',
    'WholeSaleOperationDeleteRequest',
    'WholeSaleOperationDeleteResponse',
    'WholeSaleOperationGetDiscountRequest',
    'WholeSaleOperationGetDiscountResponse',
    'WholeSaleOperationAddDiscountRequest',
    'WholeSaleOperationAddDiscountResponse',
    'WholeSaleOperationDeleteDiscountRequest',
    'WholeSaleOperationDeleteDiscountResponse',
    'WholeSaleOperationMoveOperationsRequest',
    'WholeSaleOperationMoveOperationsResponse',
    'WholeSaleOperationCopyOperationsFromDocPurchaseRequest',
    'WholeSaleOperationCopyOperationsFromDocPurchaseResponse',
    'WholeSaleOperationCopyOperationsFromDocOrderFromPartnerRequest',
    'WholeSaleOperationCopyOperationsFromDocOrderFromPartnerResponse',
    'WholeSaleOperationSetPriceByPriceTypeRequest',
    'WholeSaleOperationSetPriceByPriceTypeResponse'
]
