"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PurchaseOperation(RegosModel):
    "Модель, описывающая операцию поступления от контрагента"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции поступления от контрагента")
    document_id: int | None = PydField(default=None, description="ID документа поступления от контрагента")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    cost: _Decimal | None = PydField(default=None, description="Закупочная цена номенклатуры")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    price: _Decimal | None = PydField(default=None, description="Стоимость номенклатуры")
    order: int | None = PydField(default=None, description="Порядок операции")
    current_price: _Decimal | None = PydField(default=None, description="Текущая цена, если задано поле price_type у документа")
    last_purchase_cost: _Decimal | None = PydField(default=None, description="Стоимость последней закупки")
    description: str | None = PydField(default=None, description="Примечание")
    additional_expenses_amount: _Decimal | None = PydField(default=None, description="Сумма дополнительных расходов на операцию. Расчитывается на основании документов дополнителных операций")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class PurchaseOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    cost: _Decimal | None = PydField(default=None)
    price: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции (NULL = не задано, в БД сохраняется как NULL).\nДля версий БД ниже 363 игнорируется.")
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class PurchaseOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции поступления от контрагента")


class PurchaseOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции поступления от контрагента")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    cost: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    price: _Decimal | None = PydField(default=None, description="Стоимость номенклатуры")
    order: int | None = PydField(default=None, description="Порядок операции (null = значение не меняется, для версий БД ниже 363 игнорируется)")
    additional_expenses_amount: _Decimal | None = PydField(default=None, description="Сумма дополнительных расходов на операцию")
    description: str | None = PydField(default=None, description="Примечание")


class PurchaseOperationGet(RegosModel):
    "модель запроса операций в документе закапуки"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций поступлений от контрагентов")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class PurchaseOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PurchaseOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class SetCostByLastPurchase(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="ID документа поступления от контрагента")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DiscountOperationAdd, DiscountOperationDelete, DiscountOperationGet, DiscountOperationRegosArrayResult, DocsOperationsCopy, DocsOperationsMovement, Error, ObjectRegosObjectResult, SetPriceByPriceType_Model, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


PurchaseOperationAddDiscountRequest: TypeAlias = DiscountOperationAdd
PurchaseOperationAddDiscountResponse: TypeAlias = UpdateResult
PurchaseOperationAddRequest: TypeAlias = list[PurchaseOperationAdd]
PurchaseOperationAddResponse: TypeAlias = UpdateResult
PurchaseOperationCopyOperationsFromDocInvoiceRequest: TypeAlias = DocsOperationsCopy
PurchaseOperationCopyOperationsFromDocInvoiceResponse: TypeAlias = ObjectRegosObjectResult
PurchaseOperationCopyOperationsFromDocOrderToPartnerRequest: TypeAlias = DocsOperationsCopy
PurchaseOperationCopyOperationsFromDocOrderToPartnerResponse: TypeAlias = ObjectRegosObjectResult
PurchaseOperationCopyOperationsFromDocWholeSaleRequest: TypeAlias = DocsOperationsCopy
PurchaseOperationCopyOperationsFromDocWholeSaleResponse: TypeAlias = ObjectRegosObjectResult
PurchaseOperationDeleteDiscountRequest: TypeAlias = DiscountOperationDelete
PurchaseOperationDeleteDiscountResponse: TypeAlias = UpdateResult
PurchaseOperationDeleteRequest: TypeAlias = list[PurchaseOperationDelete]
PurchaseOperationDeleteResponse: TypeAlias = UpdateResult
PurchaseOperationEditRequest: TypeAlias = list[PurchaseOperationEdit]
PurchaseOperationEditResponse: TypeAlias = UpdateResult
PurchaseOperationGetDiscountRequest: TypeAlias = DiscountOperationGet
PurchaseOperationGetDiscountResponse: TypeAlias = DiscountOperationRegosArrayResult
PurchaseOperationGetRequest: TypeAlias = PurchaseOperationGet
PurchaseOperationGetResponse: TypeAlias = PurchaseOperationRegosOffsettedArrayResult
PurchaseOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
PurchaseOperationMoveOperationsResponse: TypeAlias = UpdateResult
PurchaseOperationSetCostByLastPurchaseRequest: TypeAlias = SetCostByLastPurchase
PurchaseOperationSetCostByLastPurchaseResponse: TypeAlias = UpdateResult
PurchaseOperationSetPriceByPriceTypeRequest: TypeAlias = SetPriceByPriceType_Model
PurchaseOperationSetPriceByPriceTypeResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['PurchaseOperation', 'PurchaseOperationAdd', 'PurchaseOperationDelete', 'PurchaseOperationEdit', 'PurchaseOperationGet', 'PurchaseOperationRegosOffsettedArrayResult', 'SetCostByLastPurchase']


__all__ = [
    'PurchaseOperation',
    'PurchaseOperationAdd',
    'PurchaseOperationDelete',
    'PurchaseOperationEdit',
    'PurchaseOperationGet',
    'PurchaseOperationRegosOffsettedArrayResult',
    'SetCostByLastPurchase',
    'PurchaseOperationGetRequest',
    'PurchaseOperationGetResponse',
    'PurchaseOperationAddRequest',
    'PurchaseOperationAddResponse',
    'PurchaseOperationEditRequest',
    'PurchaseOperationEditResponse',
    'PurchaseOperationDeleteRequest',
    'PurchaseOperationDeleteResponse',
    'PurchaseOperationSetCostByLastPurchaseRequest',
    'PurchaseOperationSetCostByLastPurchaseResponse',
    'PurchaseOperationSetPriceByPriceTypeRequest',
    'PurchaseOperationSetPriceByPriceTypeResponse',
    'PurchaseOperationGetDiscountRequest',
    'PurchaseOperationGetDiscountResponse',
    'PurchaseOperationAddDiscountRequest',
    'PurchaseOperationAddDiscountResponse',
    'PurchaseOperationDeleteDiscountRequest',
    'PurchaseOperationDeleteDiscountResponse',
    'PurchaseOperationMoveOperationsRequest',
    'PurchaseOperationMoveOperationsResponse',
    'PurchaseOperationCopyOperationsFromDocWholeSaleRequest',
    'PurchaseOperationCopyOperationsFromDocWholeSaleResponse',
    'PurchaseOperationCopyOperationsFromDocOrderToPartnerRequest',
    'PurchaseOperationCopyOperationsFromDocOrderToPartnerResponse',
    'PurchaseOperationCopyOperationsFromDocInvoiceRequest',
    'PurchaseOperationCopyOperationsFromDocInvoiceResponse'
]
