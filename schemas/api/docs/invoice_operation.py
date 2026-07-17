"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class InvoiceOperation(RegosModel):
    "Модель, описывающая операции счёт-фактуры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID счёт-фактуры")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена за единицу номенклатуры")
    amount: _Decimal | None = PydField(default=None, description="Сумма")
    total: _Decimal | None = PydField(default=None, description="Сумма к оплате")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    vat_amount: _Decimal | None = PydField(default=None, description="Сумма НДС")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате unix time")


class InvoiceOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    price: _Decimal | None = PydField(default=None)
    vat_value: _Decimal | None = PydField(default=None)


class InvoiceOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции счёт-фактуры")


class InvoiceOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции счёт-фактуры")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")


class InvoiceOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций счёт-фактур")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class InvoiceOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[InvoiceOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class InvoiceRoamingOperation(RegosModel):
    "Операция документа с роминга счёт фактур"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    name: str | None = PydField(default=None, description="наименование номенклатуры")
    icps: str | None = PydField(default=None, description="ИКПУ")
    barcode: str | None = PydField(default=None, description="штрихкод")
    package_code: str | None = PydField(default=None, description="код упаковки")
    package_name: str | None = PydField(default=None, description="наименование упаковки")
    quantity: _Decimal | None = PydField(default=None, description="количество")
    price: _Decimal | None = PydField(default=None, description="стоимость за единицу, без НДС")
    labels: list[str] | None = PydField(default=None, description="коды маркировки потребительские")
    group_labels: list[str] | None = PydField(default=None, description="коды маркировки групповые")
    transport_labels: list[str] | None = PydField(default=None, description="коды маркировки транспортные")
    origin: int | None = PydField(default=None, description="происхождение  (-1 не знадано, 0 купля-продажа, 1 собственное производство, 2 - услуги)")
    vat_rate: int | None = PydField(default=None, description="Ставка НДС")


class InvoiceRoamingOperationArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[InvoiceRoamingOperation] | Error | None = PydField(default=None, description="Объект результата.")


class InvoiceRoamingOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: str | None = PydField(default=None, description="ID счёт-фактуры в системе ЭДО")
    firm_id: int | None = PydField(default=None, description="ID предприятия")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DocsOperationsMovement, Error, SetPriceByPriceType_Model, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


InvoiceOperationAddRequest: TypeAlias = list[InvoiceOperationAdd]
InvoiceOperationAddResponse: TypeAlias = UpdateResult
InvoiceOperationDeleteRequest: TypeAlias = list[InvoiceOperationDelete]
InvoiceOperationDeleteResponse: TypeAlias = UpdateResult
InvoiceOperationEditRequest: TypeAlias = list[InvoiceOperationEdit]
InvoiceOperationEditResponse: TypeAlias = UpdateResult
InvoiceOperationGetOperationsFromRoamingRequest: TypeAlias = InvoiceRoamingOperationGet
InvoiceOperationGetOperationsFromRoamingResponse: TypeAlias = InvoiceRoamingOperationArrayRegosObjectResult
InvoiceOperationGetRequest: TypeAlias = InvoiceOperationGet
InvoiceOperationGetResponse: TypeAlias = InvoiceOperationRegosOffsettedArrayResult
InvoiceOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
InvoiceOperationMoveOperationsResponse: TypeAlias = UpdateResult
InvoiceOperationSetPriceByPriceTypeRequest: TypeAlias = SetPriceByPriceType_Model
InvoiceOperationSetPriceByPriceTypeResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['InvoiceOperation', 'InvoiceOperationAdd', 'InvoiceOperationDelete', 'InvoiceOperationEdit', 'InvoiceOperationGet', 'InvoiceOperationRegosOffsettedArrayResult', 'InvoiceRoamingOperation', 'InvoiceRoamingOperationArrayRegosObjectResult', 'InvoiceRoamingOperationGet']


__all__ = [
    'InvoiceOperation',
    'InvoiceOperationAdd',
    'InvoiceOperationDelete',
    'InvoiceOperationEdit',
    'InvoiceOperationGet',
    'InvoiceOperationRegosOffsettedArrayResult',
    'InvoiceRoamingOperation',
    'InvoiceRoamingOperationArrayRegosObjectResult',
    'InvoiceRoamingOperationGet',
    'InvoiceOperationGetRequest',
    'InvoiceOperationGetResponse',
    'InvoiceOperationAddRequest',
    'InvoiceOperationAddResponse',
    'InvoiceOperationEditRequest',
    'InvoiceOperationEditResponse',
    'InvoiceOperationDeleteRequest',
    'InvoiceOperationDeleteResponse',
    'InvoiceOperationSetPriceByPriceTypeRequest',
    'InvoiceOperationSetPriceByPriceTypeResponse',
    'InvoiceOperationMoveOperationsRequest',
    'InvoiceOperationMoveOperationsResponse',
    'InvoiceOperationGetOperationsFromRoamingRequest',
    'InvoiceOperationGetOperationsFromRoamingResponse'
]
