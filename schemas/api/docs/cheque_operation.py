"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ChequePosition(RegosModel):
    "модель позиции чека (список номенлкатур в чеке)"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="идентификатор (позиции)")
    has_storno: bool | None = PydField(default=None, description="флаг что это позиция сторнирована")
    storno_uuid: str | None = PydField(default=None, description="идетификатор сторнированного позиции.\n           связка/ссылка сторнирующей позиции к сторнированному")
    stock_id: int | None = PydField(default=None, description="id склада, куда относится позиция")
    item_id: int | None = PydField(default=None, description="id товара позиции")
    group_id: int | None = PydField(default=None, description="id группы товара позиции")
    item: Item | None = PydField(default=None, description="данные о товаре позиции")
    order: int | None = PydField(default=None, description="порядковый номер позиции. (для сортировки позиции)")
    sort_order: int | None = PydField(default=None)
    price: _Decimal | None = PydField(default=None, description="цена позиции")
    price2: _Decimal | None = PydField(default=None, description="цена без скидки позиции")
    vat_value: _Decimal | None = PydField(default=None, description="значение НДС")
    label: str | None = PydField(default=None, description="маркировка")
    barcode: str | None = PydField(default=None, description="штрих код")
    document_uuid: str | None = PydField(default=None, description="идентификатор чека. (связка к чеку)")
    quantity: _Decimal | None = PydField(default=None, description="кол-во позиции")
    promo_id: int | None = PydField(default=None, description="id промо-акции (если есть) применённый к этой позиции")
    order_opr_id: int | None = PydField(default=None, description="id позиции заказа доставки (если есть)")
    order_opr_quantity: _Decimal | None = PydField(default=None, description="кол-во позиции заказа доставки (если есть)")


class ChequePositionAdd(RegosModel):
    "модель для добавления новой позиции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    document_uuid: str | None = PydField(default=None, description="UUID кассового чека")
    quantity: _Decimal | None = PydField(default=None, description="Количество позиций в чеке")
    label: str | None = PydField(default=None, description="Маркировка")


class ChequePositionArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ChequePosition] | Error | None = PydField(default=None, description="Объект результата.")


class ChequePositionGet(RegosModel):
    "модель для получения позиции чека"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuids: list[str] | None = PydField(default=None, description="Массив UUID позиций кассового чека")
    exclude_storno: bool | None = PydField(default=None, description="Исключать сторнированную и сторнирующую позиции")
    document_uuid: str | None = PydField(default=None, description="UUID кассового чека")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")


class ChequePosition_AddByBarcode(RegosModel):
    "модель для добавления новой позиции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_uuid: str | None = PydField(default=None, description="UUID кассового чека")
    barcode: str | None = PydField(default=None, description="Штрих-код номенклатуры")


class ChequePosition_Storno(RegosModel):
    "модель для сторнирования позиции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID сторнируемой позиции кассового чека")
    document_uuid: str | None = PydField(default=None, description="UUID кассового чека")


class ChequePostion_Edit(RegosModel):
    "редактирование позиции. (кол-во и цены)"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID позиции")
    quantity: _Decimal | None = PydField(default=None, description="Новое количество позиции номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Новая цена позиции номенклатуры")
    label: str | None = PydField(default=None, description="Маркировка")


class Cheque_SetRowPercentDiscount(RegosModel):
    "установка %-скидки на позицию"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID позиции кассового чека")
    percent: _Decimal | None = PydField(default=None, description="Процент скидки")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, Insert_uuid_Result, UpdateResult
from schemas.api.docs.doc_cheque import (
    DocChequeOperation as _DocChequeOperation,
    DocChequeOperationGet as _DocChequeOperationGet,
    DocChequeOperationRegosArrayResult as _DocChequeOperationRegosArrayResult,
)
from schemas.api.references.item import Item


ChequeOperationAddByBarcodeRequest: TypeAlias = ChequePosition_AddByBarcode
ChequeOperationAddByBarcodeResponse: TypeAlias = Insert_uuid_Result
ChequeOperationAddRequest: TypeAlias = ChequePositionAdd
ChequeOperationAddResponse: TypeAlias = Insert_uuid_Result
ChequeOperationEditRequest: TypeAlias = ChequePostion_Edit
ChequeOperationEditResponse: TypeAlias = UpdateResult
ChequeOperationGetRequest: TypeAlias = ChequePositionGet
ChequeOperationGetResponse: TypeAlias = ChequePositionArrayRegosObjectResult
ChequeOperationSetPercentDiscountRequest: TypeAlias = Cheque_SetRowPercentDiscount
ChequeOperationSetPercentDiscountResponse: TypeAlias = UpdateResult
ChequeOperationStornoRequest: TypeAlias = ChequePosition_Storno
ChequeOperationStornoResponse: TypeAlias = UpdateResult
DocChequeOperation: TypeAlias = _DocChequeOperation
DocChequeOperationGetRequest: TypeAlias = _DocChequeOperationGet
DocChequeOperationGetResponse: TypeAlias = _DocChequeOperationRegosArrayResult


_MODEL_NAMES = ['ChequePosition', 'ChequePositionAdd', 'ChequePositionArrayRegosObjectResult', 'ChequePositionGet', 'ChequePosition_AddByBarcode', 'ChequePosition_Storno', 'ChequePostion_Edit', 'Cheque_SetRowPercentDiscount']


__all__ = [
    'ChequePosition',
    'ChequePositionAdd',
    'ChequePositionArrayRegosObjectResult',
    'ChequePositionGet',
    'ChequePosition_AddByBarcode',
    'ChequePosition_Storno',
    'ChequePostion_Edit',
    'Cheque_SetRowPercentDiscount',
    'ChequeOperationGetRequest',
    'ChequeOperationGetResponse',
    'ChequeOperationAddRequest',
    'ChequeOperationAddResponse',
    'ChequeOperationAddByBarcodeRequest',
    'ChequeOperationAddByBarcodeResponse',
    'ChequeOperationEditRequest',
    'ChequeOperationEditResponse',
    'ChequeOperationStornoRequest',
    'ChequeOperationStornoResponse',
    'ChequeOperationSetPercentDiscountRequest',
    'ChequeOperationSetPercentDiscountResponse',
    'DocChequeOperation',
    'DocChequeOperationGetRequest',
    'DocChequeOperationGetResponse'
]
