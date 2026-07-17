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


# ==== Модели ====


class DocMovement(BaseSchema):
    """Рид-модель документа перемещения."""

    model_config = ConfigDict(extra="allow")

    id: int = PydField(..., ge=1, description="ID документа перемещения.")
    date: Optional[int] = PydField(
        default=None, ge=0, description="Дата документа (unixtime, сек)."
    )
    code: Optional[str] = PydField(default=None, description="Номер документа.")
    partner: Optional[Partner] = PydField(
        default=None, description="Контрагент документа."
    )
    stock: Optional[Stock] = PydField(
        default=None, description="Основной склад документа."
    )
    stock_sender: Optional[Stock] = PydField(
        default=None, description="Склад-отправитель документа."
    )
    stock_receiver: Optional[Stock] = PydField(
        default=None, description="Склад-получатель документа."
    )
    contract: Optional[str] = PydField(
        default=None, description="Договор, если указан."
    )
    seller: Optional[User] = PydField(
        default=None, description="Продающий сотрудник документа."
    )
    currency: Optional[Currency] = PydField(
        default=None, description="Валюта документа."
    )
    description: Optional[str] = PydField(
        default=None, description="Комментарий к документу."
    )
    amount: Optional[Decimal] = PydField(default=None, description="Сумма документа.")
    exchange_rate: Optional[Decimal] = PydField(
        default=None, description="Курс валюты документа."
    )
    additional_expenses_amount: Optional[Decimal] = PydField(
        default=None, description="Дополнительные расходы документа."
    )
    vat_calculation_type: Optional[VatCalculationType] = PydField(
        default=None, description="Тип расчёта НДС."
    )
    attached_user: Optional[User] = PydField(
        default=None, description="Прикреплённый пользователь."
    )
    price_type: Optional[PriceType] = PydField(
        default=None, description="Тип цены документа."
    )
    blocked: Optional[bool] = PydField(
        default=None, description="Документ заблокирован."
    )
    current_user_blocked: Optional[bool] = PydField(
        default=None, description="Документ заблокирован текущим пользователем."
    )
    performed: Optional[bool] = PydField(default=None, description="Документ проведён.")
    deleted_mark: Optional[bool] = PydField(
        default=None, description="Документ помечен на удаление."
    )
    last_update: Optional[int] = PydField(
        default=None, ge=0, description="Метка последнего изменения (unixtime, сек)."
    )


class DocMovementSortOrder(BaseSchema):
    """Параметры сортировки списка документов перемещения."""

    model_config = ConfigDict(extra="forbid")

    column: Optional[str] = PydField(
        default=None, description="Поле сортировки документа."
    )
    direction: Optional[str] = PydField(
        default=None, description="Направление сортировки (ASC|DESC)."
    )


class DocMovementGetRequest(BaseSchema):
    """Фильтры выборки документов перемещения."""

    model_config = ConfigDict(extra="forbid")

    start_date: Optional[int] = PydField(
        default=None, ge=0, description="Начало периода (unixtime, сек)."
    )
    end_date: Optional[int] = PydField(
        default=None, ge=0, description="Конец периода (unixtime, сек)."
    )
    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по идентификаторам документов."
    )
    firm_sender_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по фирмам-отправителям."
    )
    firm_receiver_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по фирмам-получателям."
    )
    stock_sender_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по складам-отправителям."
    )
    stock_receiver_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по складам-получателям."
    )
    attached_user_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по прикреплённым пользователям."
    )
    performed: Optional[bool] = PydField(
        default=None, description="Фильтр по проведённым документам."
    )
    blocked: Optional[bool] = PydField(
        default=None, description="Фильтр по заблокированным документам."
    )
    deleted_mark: Optional[bool] = PydField(
        default=None, description="Фильтр по пометке на удаление."
    )
    search: Optional[str] = PydField(
        default=None, description="Строка поиска по документам."
    )
    sort_orders: Optional[List[DocMovementSortOrder]] = PydField(
        default=None, description="Набор правил сортировки."
    )
    limit: Optional[int] = PydField(
        default=None, ge=1, description="Лимит записей в ответе."
    )
    offset: Optional[int] = PydField(
        default=None, ge=0, description="Смещение выборки."
    )

    @model_validator(mode="after")
    def _check_dates(cls, values: "DocMovementGetRequest"):
        if (
            values.start_date
            and values.end_date
            and values.end_date < values.start_date
        ):
            raise ValueError("end_date не может быть меньше start_date")
        return values


class DocMovementGetResponse(APIBaseResponse[List[DocMovement]]):
    """Ответ на запрос /v1/DocMovement/Get."""

    model_config = ConfigDict(extra="ignore")


class DocMovementAddRequest(BaseSchema):
    """
    Параметры создания документа перемещения.

    Пример тела запроса:
    {
        "date": 1534151629,
        "stock_sender_id": 2,
        "stock_receiver_id": 3,
        "description": "example",
        "attached_user_id": 2
    }
    """

    model_config = ConfigDict(extra="forbid")

    date: int = PydField(..., ge=0, description="Дата документа (unixtime, сек).")
    stock_sender_id: int = PydField(..., ge=1, description="ID склада-отправителя.")
    stock_receiver_id: int = PydField(..., ge=1, description="ID склада-получателя.")
    description: Optional[str] = PydField(
        default=None, description="Описание документа."
    )
    attached_user_id: Optional[int] = PydField(
        default=None, ge=1, description="ID прикреплённого пользователя."
    )


__all__ = [
    "DocMovement",
    "DocMovementGetRequest",
    "DocMovementGetResponse",
    "DocMovementSortOrder",
    "DocMovementAddRequest",
]
