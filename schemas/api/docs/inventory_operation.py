"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class InventoryOperation(RegosModel):
    "Модель, описывающая операции инвентаризации"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    document_id: int | None = PydField(default=None, description="ID документа инвентаризации")
    datetime: int | None = PydField(default=None, description="Дата в формате unix time, на которую берутся данные по количеству")
    item: Item | None = PydField(default=None, description="Номенклатура")
    actual_quantity: _Decimal | None = PydField(default=None, description="Актуальное количество номенклатуры")
    registered_quantity: _Decimal | None = PydField(default=None, description="Зарегестрированное количество номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    last_purchase_cost: _Decimal | None = PydField(default=None, description="Стоимость последней закупки")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате unix time")


class InventoryOperationAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    actual_quantity: _Decimal | None = PydField(default=None)
    datetime: int | None = PydField(default=None, description="дата, на которую берутся данные по количеству")
    update_actual_quantity: bool | None = PydField(default=None, description="Если вручную изменяется это и значение должно установиться, если update_actual_quantity=true.\nВ ином случае будет отправляемое actual_quantity + actual_quantity в базе !")


class InventoryOperationAddBulk(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="ID документа инвентаризации")
    group_ids: list[int] | None = PydField(default=None, description="Массив ID групп номенклатуры")
    department_ids: list[int] | None = PydField(default=None, description="Массив ID разделов номенклатуры")
    actual_quantity: _Decimal | None = PydField(default=None, description="Актуальное количество номенклатуры. По умолчанию: 0")
    update_actual_quantity: bool | None = PydField(default=None, description="Обновление количества номенклатуры: true - Обновлять, false - Не обновлять, а добавлять к существующему количеству")


class InventoryOperationDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class InventoryOperationEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)
    actual_quantity: _Decimal | None = PydField(default=None)
    update_actual_quantity: bool | None = PydField(default=None, description="Если вручную изменяется это и значение должно установиться, если update_actual_quantity=true.\nВ ином случае будет отправляемое actual_quantity + actual_quantity в базе !")
    price: _Decimal | None = PydField(default=None)


class InventoryOperationGet(RegosModel):
    "модель для получения списка операций по инветоризации"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID операций инвентаризации")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов инвентаризации")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item/name - Наименование номенклатуры, Item/articul - Артикул номенклатуры, Item/code - Код номенклатуры")
    only_deviation: bool | None = PydField(default=None, description="Статус отображения отклонений: true - Показывать только отклонения, false - Показывать все")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class InventoryOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[InventoryOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DocsOperationsMovement, Error, SetPriceByPriceType_Model, UpdateResult
from schemas.api.references.item import Item


InventoryOperationAddBulkRequest: TypeAlias = InventoryOperationAddBulk
InventoryOperationAddBulkResponse: TypeAlias = UpdateResult
InventoryOperationAddRequest: TypeAlias = list[InventoryOperationAdd]
InventoryOperationAddResponse: TypeAlias = UpdateResult
InventoryOperationDeleteRequest: TypeAlias = list[InventoryOperationDelete]
InventoryOperationDeleteResponse: TypeAlias = UpdateResult
InventoryOperationEditRequest: TypeAlias = list[InventoryOperationEdit]
InventoryOperationEditResponse: TypeAlias = UpdateResult
InventoryOperationGetRequest: TypeAlias = InventoryOperationGet
InventoryOperationGetResponse: TypeAlias = InventoryOperationRegosOffsettedArrayResult
InventoryOperationMoveOperationsRequest: TypeAlias = DocsOperationsMovement
InventoryOperationMoveOperationsResponse: TypeAlias = UpdateResult
InventoryOperationSetPriceByPriceTypeRequest: TypeAlias = SetPriceByPriceType_Model
InventoryOperationSetPriceByPriceTypeResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['InventoryOperation', 'InventoryOperationAdd', 'InventoryOperationAddBulk', 'InventoryOperationDelete', 'InventoryOperationEdit', 'InventoryOperationGet', 'InventoryOperationRegosOffsettedArrayResult']


__all__ = [
    'InventoryOperation',
    'InventoryOperationAdd',
    'InventoryOperationAddBulk',
    'InventoryOperationDelete',
    'InventoryOperationEdit',
    'InventoryOperationGet',
    'InventoryOperationRegosOffsettedArrayResult',
    'InventoryOperationGetRequest',
    'InventoryOperationGetResponse',
    'InventoryOperationAddRequest',
    'InventoryOperationAddResponse',
    'InventoryOperationAddBulkRequest',
    'InventoryOperationAddBulkResponse',
    'InventoryOperationEditRequest',
    'InventoryOperationEditResponse',
    'InventoryOperationDeleteRequest',
    'InventoryOperationDeleteResponse',
    'InventoryOperationMoveOperationsRequest',
    'InventoryOperationMoveOperationsResponse',
    'InventoryOperationSetPriceByPriceTypeRequest',
    'InventoryOperationSetPriceByPriceTypeResponse'
]
