"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ReturnsToPartnerOperation(RegosModel):
    "Модель, описывающая операции возврата контрагенту"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа возврата")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    cost: _Decimal | None = PydField(default=None, description="Стоимость возврата номенклатуры")
    order: int | None = PydField(default=None, description="Порядок операции")
    last_purchase_cost: _Decimal | None = PydField(default=None, description="Стоимость последней закупки")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    description: str | None = PydField(default=None, description="Примечание")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class ReturnsToPartnerOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    cost: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции (NULL = не задано, в БД сохраняется как NULL).\nДля версий БД ниже 363 игнорируется.")
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class ReturnsToPartnerOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class ReturnsToPartnerOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None)
    cost: _Decimal | None = PydField(default=None)
    order: int | None = PydField(default=None, description="Порядок операции. Если NULL, значение в БД не меняется.\nДля версий БД ниже 363 игнорируется.")
    vat_value: _Decimal | None = PydField(default=None)
    description: str | None = PydField(default=None, description="примечание")


class ReturnsToPartnerOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций возврата контрагенту")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class ReturnsToPartnerOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ReturnsToPartnerOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class SetCostByLastReturnToPartner(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="ID документа возврата контрагенту")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DiscountOperationAdd, DiscountOperationDelete, DiscountOperationGet, DiscountOperationRegosArrayResult, DocsOperationsMovement, Error, UpdateResult, VatCalculationTypeEnum
from schemas.api.references.item import Item


ReturnsToPartnerOperationAddDiscountRequest: TypeAlias = DiscountOperationAdd
ReturnsToPartnerOperationAddDiscountResponse: TypeAlias = UpdateResult
ReturnsToPartnerOperationAddRequest: TypeAlias = list[ReturnsToPartnerOperationAdd]
ReturnsToPartnerOperationAddResponse: TypeAlias = UpdateResult
ReturnsToPartnerOperationDeleteDiscountRequest: TypeAlias = DiscountOperationDelete
ReturnsToPartnerOperationDeleteDiscountResponse: TypeAlias = UpdateResult
ReturnsToPartnerOperationDeleteRequest: TypeAlias = list[ReturnsToPartnerOperationDelete]
ReturnsToPartnerOperationDeleteResponse: TypeAlias = UpdateResult
ReturnsToPartnerOperationEditRequest: TypeAlias = list[ReturnsToPartnerOperationEdit]
ReturnsToPartnerOperationEditResponse: TypeAlias = UpdateResult
ReturnsToPartnerOperationGetDiscountRequest: TypeAlias = DiscountOperationGet
ReturnsToPartnerOperationGetDiscountResponse: TypeAlias = DiscountOperationRegosArrayResult
ReturnsToPartnerOperationGetRequest: TypeAlias = ReturnsToPartnerOperationGet
ReturnsToPartnerOperationGetResponse: TypeAlias = ReturnsToPartnerOperationRegosOffsettedArrayResult
ReturnsToPartnerOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
ReturnsToPartnerOperationMoveOperationsResponse: TypeAlias = UpdateResult
ReturnsToPartnerOperationSetCostByLastPurchaseRequest: TypeAlias = SetCostByLastReturnToPartner
ReturnsToPartnerOperationSetCostByLastPurchaseResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['ReturnsToPartnerOperation', 'ReturnsToPartnerOperationAdd', 'ReturnsToPartnerOperationDelete', 'ReturnsToPartnerOperationEdit', 'ReturnsToPartnerOperationGet', 'ReturnsToPartnerOperationRegosOffsettedArrayResult', 'SetCostByLastReturnToPartner']


__all__ = [
    'ReturnsToPartnerOperation',
    'ReturnsToPartnerOperationAdd',
    'ReturnsToPartnerOperationDelete',
    'ReturnsToPartnerOperationEdit',
    'ReturnsToPartnerOperationGet',
    'ReturnsToPartnerOperationRegosOffsettedArrayResult',
    'SetCostByLastReturnToPartner',
    'ReturnsToPartnerOperationGetRequest',
    'ReturnsToPartnerOperationGetResponse',
    'ReturnsToPartnerOperationAddRequest',
    'ReturnsToPartnerOperationAddResponse',
    'ReturnsToPartnerOperationEditRequest',
    'ReturnsToPartnerOperationEditResponse',
    'ReturnsToPartnerOperationDeleteRequest',
    'ReturnsToPartnerOperationDeleteResponse',
    'ReturnsToPartnerOperationSetCostByLastPurchaseRequest',
    'ReturnsToPartnerOperationSetCostByLastPurchaseResponse',
    'ReturnsToPartnerOperationGetDiscountRequest',
    'ReturnsToPartnerOperationGetDiscountResponse',
    'ReturnsToPartnerOperationAddDiscountRequest',
    'ReturnsToPartnerOperationAddDiscountResponse',
    'ReturnsToPartnerOperationDeleteDiscountRequest',
    'ReturnsToPartnerOperationDeleteDiscountResponse',
    'ReturnsToPartnerOperationMoveOperationsRequest',
    'ReturnsToPartnerOperationMoveOperationsResponse'
]
