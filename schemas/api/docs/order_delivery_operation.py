"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class OrderDeliveryOperation(RegosModel):
    "Модель, описывающая операции документа розничного заказа"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа розничного заказа")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    quantity_const: _Decimal | None = PydField(default=None, description="Количество номенклатуры, доступное на складе, указанном для заказа")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    actual_quantity: _Decimal | None = PydField(default=None, description="Актуализированное количество")
    actual_price: _Decimal | None = PydField(default=None, description="Актуализированная цена. actual_price не null, если у документа розничного заказа задан price_type и/или stock в модели\nDocOrderDelivery. Актуальное количество считается как - текущее количество минус забронированное количество")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате unix time")


class OrderDeliveryOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    item_code: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    price: _Decimal | None = PydField(default=None)


class OrderDeliveryOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции розничного заказа")


class OrderDeliveryOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции розничного заказа")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")


class OrderDeliveryOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций розничного заказа")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры, присутствующей в заказе")
    document_id: int | None = PydField(default=None, description="ID документа")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class OrderDeliveryOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[OrderDeliveryOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


OrderDeliveryOperationAddRequest: TypeAlias = list[OrderDeliveryOperationAdd]
OrderDeliveryOperationAddResponse: TypeAlias = UpdateResult
OrderDeliveryOperationDeleteRequest: TypeAlias = list[OrderDeliveryOperationDelete]
OrderDeliveryOperationDeleteResponse: TypeAlias = UpdateResult
OrderDeliveryOperationEditRequest: TypeAlias = list[OrderDeliveryOperationEdit]
OrderDeliveryOperationEditResponse: TypeAlias = UpdateResult
OrderDeliveryOperationGetRequest: TypeAlias = OrderDeliveryOperationGet
OrderDeliveryOperationGetResponse: TypeAlias = OrderDeliveryOperationRegosOffsettedArrayResult


_MODEL_NAMES = ['OrderDeliveryOperation', 'OrderDeliveryOperationAdd', 'OrderDeliveryOperationDelete', 'OrderDeliveryOperationEdit', 'OrderDeliveryOperationGet', 'OrderDeliveryOperationRegosOffsettedArrayResult']


__all__ = [
    'OrderDeliveryOperation',
    'OrderDeliveryOperationAdd',
    'OrderDeliveryOperationDelete',
    'OrderDeliveryOperationEdit',
    'OrderDeliveryOperationGet',
    'OrderDeliveryOperationRegosOffsettedArrayResult',
    'OrderDeliveryOperationGetRequest',
    'OrderDeliveryOperationGetResponse',
    'OrderDeliveryOperationAddRequest',
    'OrderDeliveryOperationAddResponse',
    'OrderDeliveryOperationEditRequest',
    'OrderDeliveryOperationEditResponse',
    'OrderDeliveryOperationDeleteRequest',
    'OrderDeliveryOperationDeleteResponse'
]
