"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class OrderToPartnerOperation(RegosModel):
    "Модель, описывающая операцию документа заказа контрагенту"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа заказа контрагенту")
    datetime: int | None = PydField(default=None, description="дата, на которую берутся данные по количеству")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    current_quantity: _Decimal | None = PydField(default=None, description="Текущие количество")
    cost: _Decimal | None = PydField(default=None, description="Цена заказа номенклатуры")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки ндс")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    description: str | None = PydField(default=None, description="Примечание")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class OrderToPartnerOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    cost: _Decimal | None = PydField(default=None)
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class OrderToPartnerOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class OrderToPartnerOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    cost: _Decimal | None = PydField(default=None)
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class OrderToPartnerOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="массив ID операций заказа контрагенту")
    item_ids: list[int] | None = PydField(default=None, description="массив ID номенклатуры в документах заказа котрагенту")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class OrderToPartnerOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[OrderToPartnerOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DocsOperationsMovement, Error, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


OrderToPartnerOperationAddRequest: TypeAlias = list[OrderToPartnerOperationAdd]
OrderToPartnerOperationAddResponse: TypeAlias = UpdateResult
OrderToPartnerOperationDeleteRequest: TypeAlias = list[OrderToPartnerOperationDelete]
OrderToPartnerOperationDeleteResponse: TypeAlias = UpdateResult
OrderToPartnerOperationEditRequest: TypeAlias = list[OrderToPartnerOperationEdit]
OrderToPartnerOperationEditResponse: TypeAlias = UpdateResult
OrderToPartnerOperationGetRequest: TypeAlias = OrderToPartnerOperationGet
OrderToPartnerOperationGetResponse: TypeAlias = OrderToPartnerOperationRegosOffsettedArrayResult
OrderToPartnerOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
OrderToPartnerOperationMoveOperationsResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['OrderToPartnerOperation', 'OrderToPartnerOperationAdd', 'OrderToPartnerOperationDelete', 'OrderToPartnerOperationEdit', 'OrderToPartnerOperationGet', 'OrderToPartnerOperationRegosOffsettedArrayResult']


__all__ = [
    'OrderToPartnerOperation',
    'OrderToPartnerOperationAdd',
    'OrderToPartnerOperationDelete',
    'OrderToPartnerOperationEdit',
    'OrderToPartnerOperationGet',
    'OrderToPartnerOperationRegosOffsettedArrayResult',
    'OrderToPartnerOperationGetRequest',
    'OrderToPartnerOperationGetResponse',
    'OrderToPartnerOperationAddRequest',
    'OrderToPartnerOperationAddResponse',
    'OrderToPartnerOperationEditRequest',
    'OrderToPartnerOperationEditResponse',
    'OrderToPartnerOperationDeleteRequest',
    'OrderToPartnerOperationDeleteResponse',
    'OrderToPartnerOperationMoveOperationsRequest',
    'OrderToPartnerOperationMoveOperationsResponse'
]
