"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class CommercialOfferOperation(RegosModel):
    "Модель, описывающая операции документа коммерческого предложения"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции документа коммерческого предложения")
    document_id: int | None = PydField(default=None, description="ID документа коммерческого предложения")
    item: Item | None = PydField(default=None, description="Номенклатура")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате Unix time")


class CommercialOfferOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    price: _Decimal | None = PydField(default=None)
    vat_value: _Decimal | None = PydField(default=None)


class CommercialOfferOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции документа коммерческого пердложения")


class CommercialOfferOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции документа коммерческого пердложения")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")


class CommercialOfferOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций документов коммерческого предложения")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class CommercialOfferOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[CommercialOfferOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


CommercialOfferOperationAddRequest: TypeAlias = list[CommercialOfferOperationAdd]
CommercialOfferOperationAddResponse: TypeAlias = UpdateResult
CommercialOfferOperationDeleteRequest: TypeAlias = list[CommercialOfferOperationDelete]
CommercialOfferOperationDeleteResponse: TypeAlias = UpdateResult
CommercialOfferOperationEditRequest: TypeAlias = list[CommercialOfferOperationEdit]
CommercialOfferOperationEditResponse: TypeAlias = UpdateResult
CommercialOfferOperationGetRequest: TypeAlias = CommercialOfferOperationGet
CommercialOfferOperationGetResponse: TypeAlias = CommercialOfferOperationRegosOffsettedArrayResult


_MODEL_NAMES = ['CommercialOfferOperation', 'CommercialOfferOperationAdd', 'CommercialOfferOperationDelete', 'CommercialOfferOperationEdit', 'CommercialOfferOperationGet', 'CommercialOfferOperationRegosOffsettedArrayResult']


__all__ = [
    'CommercialOfferOperation',
    'CommercialOfferOperationAdd',
    'CommercialOfferOperationDelete',
    'CommercialOfferOperationEdit',
    'CommercialOfferOperationGet',
    'CommercialOfferOperationRegosOffsettedArrayResult',
    'CommercialOfferOperationGetRequest',
    'CommercialOfferOperationGetResponse',
    'CommercialOfferOperationAddRequest',
    'CommercialOfferOperationAddResponse',
    'CommercialOfferOperationEditRequest',
    'CommercialOfferOperationEditResponse',
    'CommercialOfferOperationDeleteRequest',
    'CommercialOfferOperationDeleteResponse'
]
