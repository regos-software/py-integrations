"""Схемы справочника операций по номенклатуре."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.common.sort_orders import SortOrder, SortOrders
from schemas.api.references.stock import Stock


class ItemOperationDocumentType(BaseSchema):
    """Описание типа документа, инициировавшего операцию."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(None, description="ID типа документа.")
    name: Optional[str] = PydField(None, description="Наименование типа документа.")
    last_update: Optional[int] = PydField(
        None, ge=0, description="Метка последнего обновления (unixtime, сек)."
    )


class ItemOperation(BaseSchema):
    """История движения номенклатуры."""

    model_config = ConfigDict(extra="ignore")

    date: Optional[int] = PydField(
        None, ge=0, description="Дата операции (unixtime, сек)."
    )
    document_id: Optional[int] = PydField(
        None, ge=1, description="ID документа, породившего операцию."
    )
    document_type: Optional[ItemOperationDocumentType] = PydField(
        None, description="Тип документа операции."
    )
    doc_type_name: Optional[str] = PydField(
        None, description="Наименование типа документа (строка)."
    )
    doc_code: Optional[str] = PydField(
        None, description="Номер документа, связанного с операцией."
    )
    stock: Optional[Stock] = PydField(
        None, description="Склад, по которому прошла операция."
    )
    quantity: Optional[Decimal] = PydField(
        None, description="Количество номенклатуры в операции."
    )
    cost: Optional[Decimal] = PydField(None, description="Себестоимость в операции.")
    additional_expenses_amount: Optional[Decimal] = PydField(
        None, description="Сумма дополнительных расходов."
    )
    price: Optional[Decimal] = PydField(None, description="Цена по документу.")
    price2: Optional[Decimal] = PydField(
        None, description="Дополнительная цена (если есть)."
    )
    exchange_rate: Optional[Decimal] = PydField(
        None, description="Использованный курс валюты."
    )
    positive: Optional[bool] = PydField(
        None, description="Признак прихода (True) или расхода (False)."
    )
    vat_value: Optional[Decimal] = PydField(None, description="Сумма НДС.")
    vat_calculation_type: Optional[str] = PydField(
        None,
        description="Способ расчёта НДС (напр. Include / Exclude).",
    )


class ItemOperationGetRequest(BaseSchema):
    """Параметры запроса /v1/ItemOperation/Get."""

    model_config = ConfigDict(extra="forbid")

    item_id: int = PydField(..., ge=1, description="ID номенклатуры.")
    stock_ids: Optional[List[int]] = PydField(
        None, description="Массив ID складов для фильтрации."
    )
    firm_ids: Optional[List[int]] = PydField(
        None, description="Массив ID предприятий для фильтрации."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default_factory=lambda: [SortOrder(column="date", direction="desc")],
        description="Правила сортировки выборки.",
    )
    start_date: Optional[int] = PydField(
        None, ge=0, description="Начало периода (unixtime, сек)."
    )
    end_date: Optional[int] = PydField(
        None, ge=0, description="Окончание периода (unixtime, сек)."
    )
    limit: Optional[int] = PydField(
        None, ge=1, description="Количество записей в ответе."
    )
    offset: Optional[int] = PydField(None, ge=0, description="Смещение для пагинации.")


class ItemOperationGetResponse(APIBaseResponse[List[ItemOperation]]):
    """Ответ на запрос /v1/ItemOperation/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "ItemOperationDocumentType",
    "ItemOperation",
    "ItemOperationGetRequest",
    "ItemOperationGetResponse",
]
