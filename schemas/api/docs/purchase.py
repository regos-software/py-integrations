"""Схемы документов поступлений."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, model_validator

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.partner import Partner
from schemas.api.references.price_type import PriceType
from schemas.api.references.stock import Stock
from schemas.api.references.tax import VatCalculationType


class DocPurchase(BaseSchema):
    """Рид-модель документа поступления."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="ID документа.")
    date: int = PydField(..., ge=0, description="Дата документа (Unix).")
    code: str = PydField(..., description="Номер документа.")
    partner: Partner = PydField(..., description="Контрагент.")
    stock: Stock = PydField(..., description="Склад, на который поступает товар.")
    currency: Currency = PydField(..., description="Валюта документа.")
    description: Optional[str] = PydField(
        default=None, description="Комментарий к документу."
    )
    amount: Decimal = PydField(..., description="Сумма документа.")
    exchange_rate: Decimal = PydField(..., description="Курс валюты.")
    additional_expenses_amount: Decimal = PydField(
        ..., description="Дополнительные расходы."
    )
    vat_calculation_type: VatCalculationType = PydField(
        ..., description="Тип расчёта НДС."
    )
    attached_user: Optional[User] = PydField(
        default=None, description="Прикреплённый пользователь."
    )
    price_type: Optional[PriceType] = PydField(default=None, description="Тип цены.")
    blocked: bool = PydField(..., description="Документ заблокирован.")
    current_user_blocked: Optional[bool] = PydField(
        default=None, description="Текущий пользователь заблокировал документ."
    )
    performed: bool = PydField(..., description="Документ проведён.")
    deleted_mark: bool = PydField(..., description="Документ помечен на удаление.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего изменения (Unix)."
    )


class DocPurchaseSortOrder(BaseSchema):
    """Пара сортировки для списка документов."""

    model_config = ConfigDict(extra="forbid")

    column: Optional[str] = PydField(
        default=None, description="Название колонки для сортировки."
    )
    direction: Optional[str] = PydField(
        default=None, description="Направление сортировки (ASC|DESC)."
    )


class DocPurchaseGetRequest(BaseSchema):
    """Фильтры получения документов поступления."""

    model_config = ConfigDict(extra="forbid")

    start_date: Optional[int] = PydField(
        default=None, ge=0, description="Начало периода (Unix)."
    )
    end_date: Optional[int] = PydField(
        default=None, ge=0, description="Конец периода (Unix)."
    )
    ids: Optional[List[int]] = PydField(
        default=None, description="Список ID документов."
    )
    firm_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID фирм."
    )
    stock_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID складов."
    )
    partner_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID контрагентов."
    )
    contract_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID договоров."
    )
    attached_user_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID прикреплённых пользователей."
    )
    vat_calculation_type: Optional[VatCalculationType] = PydField(
        default=None, description="Тип расчёта НДС."
    )
    performed: Optional[bool] = PydField(
        default=None, description="Фильтр по проведённым документам."
    )
    blocked: Optional[bool] = PydField(
        default=None, description="Фильтр по заблокированным документам."
    )
    deleted_mark: Optional[bool] = PydField(
        default=None, description="Фильтр по пометке удаления."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по номеру или описанию."
    )
    sort_orders: Optional[List[DocPurchaseSortOrder]] = PydField(
        default=None, description="Список правил сортировки."
    )
    limit: Optional[int] = PydField(
        default=None, ge=1, description="Количество записей в выдаче."
    )
    offset: Optional[int] = PydField(
        default=None, ge=0, description="Смещение для пагинации."
    )

    @model_validator(mode="after")
    def _validate_dates(cls, values: "DocPurchaseGetRequest"):
        if (
            values.start_date
            and values.end_date
            and values.end_date < values.start_date
        ):
            raise ValueError("end_date не может быть меньше start_date")
        return values


class DocPurchaseGetResponse(APIBaseResponse[List[DocPurchase]]):
    """Ответ на запрос /v1/DocPurchase/Get."""

    model_config = ConfigDict(extra="ignore")


class DocPurchaseAddRequest(BaseSchema):
    """Модель для добавления документа поступления."""

    model_config = ConfigDict(extra="forbid")

    date: int = PydField(..., ge=0, description="Дата документа (Unix).")
    partner_id: int = PydField(..., ge=1, description="ID контрагента.")
    stock_id: int = PydField(..., ge=1, description="ID склада.")
    currency_id: int = PydField(..., ge=1, description="ID валюты.")
    contract_id: Optional[int] = PydField(
        default=None, ge=1, description="ID договора."
    )
    exchange_rate: Optional[Decimal] = PydField(
        default=None, description="Курс валюты."
    )
    description: Optional[str] = PydField(
        default=None, description="Комментарий к документу."
    )
    vat_calculation_type: Optional[VatCalculationType] = PydField(
        default=None, description="Тип расчёта НДС."
    )
    attached_user_id: int = PydField(
        ..., ge=1, description="ID прикреплённого пользователя."
    )
    price_type_id: Optional[int] = PydField(
        default=None, ge=1, description="ID типа цены."
    )


__all__ = [
    "DocPurchase",
    "DocPurchaseGetRequest",
    "DocPurchaseGetResponse",
    "DocPurchaseSortOrder",
    "DocPurchaseAddRequest",
]
