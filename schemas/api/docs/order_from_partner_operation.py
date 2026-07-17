"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class OrderFromPartnerOperation(RegosModel):
    "Модель, описывающая операцию заказа от контрагента"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа заказа от контрагента")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    current_quantity: _Decimal | None = PydField(default=None, description="Текущие количество")
    price: _Decimal | None = PydField(default=None, description="Цена со скидкой")
    price2: _Decimal | None = PydField(default=None, description="Цена без скидки")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки ндс")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    description: str | None = PydField(default=None, description="Примечание")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class OrderFromPartnerOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    price: _Decimal | None = PydField(default=None)
    price2: _Decimal | None = PydField(default=None, description="Цена без скидки")
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class OrderFromPartnerOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class OrderFromPartnerOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    price: _Decimal | None = PydField(default=None)
    price2: _Decimal | None = PydField(default=None, description="Цена без скидки")
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class OrderFromPartnerOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций заказа от контрагента")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class OrderFromPartnerOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[OrderFromPartnerOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DiscountOperationAdd, DiscountOperationDelete, DiscountOperationGet, DiscountOperationRegosArrayResult, DocsOperationsMovement, Error, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


OrderFromPartnerOperationAddDiscountRequest: TypeAlias = DiscountOperationAdd
OrderFromPartnerOperationAddDiscountResponse: TypeAlias = UpdateResult
OrderFromPartnerOperationAddRequest: TypeAlias = list[OrderFromPartnerOperationAdd]
OrderFromPartnerOperationAddResponse: TypeAlias = UpdateResult
OrderFromPartnerOperationDeleteDiscountRequest: TypeAlias = DiscountOperationDelete
OrderFromPartnerOperationDeleteDiscountResponse: TypeAlias = UpdateResult
OrderFromPartnerOperationDeleteRequest: TypeAlias = list[OrderFromPartnerOperationDelete]
OrderFromPartnerOperationDeleteResponse: TypeAlias = UpdateResult
OrderFromPartnerOperationEditRequest: TypeAlias = list[OrderFromPartnerOperationEdit]
OrderFromPartnerOperationEditResponse: TypeAlias = UpdateResult
OrderFromPartnerOperationGetDiscountRequest: TypeAlias = DiscountOperationGet
OrderFromPartnerOperationGetDiscountResponse: TypeAlias = DiscountOperationRegosArrayResult
OrderFromPartnerOperationGetRequest: TypeAlias = OrderFromPartnerOperationGet
OrderFromPartnerOperationGetResponse: TypeAlias = OrderFromPartnerOperationRegosOffsettedArrayResult
OrderFromPartnerOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
OrderFromPartnerOperationMoveOperationsResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['OrderFromPartnerOperation', 'OrderFromPartnerOperationAdd', 'OrderFromPartnerOperationDelete', 'OrderFromPartnerOperationEdit', 'OrderFromPartnerOperationGet', 'OrderFromPartnerOperationRegosOffsettedArrayResult']


__all__ = [
    'OrderFromPartnerOperation',
    'OrderFromPartnerOperationAdd',
    'OrderFromPartnerOperationDelete',
    'OrderFromPartnerOperationEdit',
    'OrderFromPartnerOperationGet',
    'OrderFromPartnerOperationRegosOffsettedArrayResult',
    'OrderFromPartnerOperationGetRequest',
    'OrderFromPartnerOperationGetResponse',
    'OrderFromPartnerOperationAddRequest',
    'OrderFromPartnerOperationAddResponse',
    'OrderFromPartnerOperationEditRequest',
    'OrderFromPartnerOperationEditResponse',
    'OrderFromPartnerOperationDeleteRequest',
    'OrderFromPartnerOperationDeleteResponse',
    'OrderFromPartnerOperationMoveOperationsRequest',
    'OrderFromPartnerOperationMoveOperationsResponse',
    'OrderFromPartnerOperationGetDiscountRequest',
    'OrderFromPartnerOperationGetDiscountResponse',
    'OrderFromPartnerOperationAddDiscountRequest',
    'OrderFromPartnerOperationAddDiscountResponse',
    'OrderFromPartnerOperationDeleteDiscountRequest',
    'OrderFromPartnerOperationDeleteDiscountResponse'
]
