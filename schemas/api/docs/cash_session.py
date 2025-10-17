"""Схемы кассовых сессий."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, model_validator

from schemas.api.base import BaseSchema
from schemas.api.rbac.user import User


class DocCashSessionSortColumn(str, Enum):
    """Доступные колонки сортировки кассовых сессий."""

    Uuid = "Uuid"
    Code = "Code"
    OperatingCashId = "OperatingCashId"
    StartDate = "StartDate"
    StartUserName = "StartUserName"
    StartAmount = "StartAmount"
    CloseDate = "CloseDate"
    CloseUserName = "CloseUserName"
    Closed = "Closed"
    CloseAmount = "CloseAmount"
    LastUpdate = "LastUpdate"


class SortDirection(str, Enum):
    """Направление сортировки."""

    ASC = "ASC"
    DESC = "DESC"


class DocCashSession(BaseSchema):
    """Рид-модель кассовой сессии."""

    model_config = ConfigDict(extra="ignore")

    uuid: str = PydField(..., description="UUID кассовой сессии.")
    code: str = PydField(..., description="Номер (код) кассовой сессии.")
    operating_cash_id: int = PydField(..., ge=1, description="ID кассы.")
    start_date: int = PydField(..., ge=0, description="Дата открытия (Unix).")
    start_user: Optional[User] = PydField(
        default=None, description="Пользователь, открывший сессию."
    )
    start_amount: Decimal = PydField(..., description="Сумма при открытии.")
    close_date: Optional[int] = PydField(
        default=None, ge=0, description="Дата закрытия (Unix)."
    )
    close_user: Optional[User] = PydField(
        default=None, description="Пользователь, закрывший сессию."
    )
    closed: bool = PydField(..., description="Признак закрытой сессии.")
    close_amount: Optional[Decimal] = PydField(
        default=None, description="Сумма при закрытии."
    )
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего изменения (Unix)."
    )


class SortOrder(BaseSchema):
    """Правило сортировки кассовых сессий."""

    model_config = ConfigDict(extra="forbid")

    column: DocCashSessionSortColumn = PydField(..., description="Колонка сортировки.")
    direction: SortDirection = PydField(
        ..., description="Направление сортировки (ASC|DESC)."
    )


class DocCashSessionGetRequest(BaseSchema):
    """Фильтры получения кассовых сессий."""

    model_config = ConfigDict(extra="forbid")

    uuids: Optional[List[str]] = PydField(
        default=None, description="Фильтр по списку UUID."
    )
    operating_cash_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку ID касс."
    )
    start_date: Optional[int] = PydField(
        default=None, ge=0, description="Начало периода (Unix)."
    )
    end_date: Optional[int] = PydField(
        default=None, ge=0, description="Конец периода (Unix)."
    )
    is_agregated: Optional[bool] = PydField(
        default=None, description="Возвращать агрегированные данные."
    )
    is_close: Optional[bool] = PydField(
        default=None, description="Фильтр по закрытым сессиям."
    )
    open_user_id: Optional[int] = PydField(
        default=None, ge=1, description="ID пользователя, открывшего сессию."
    )
    close_user_id: Optional[int] = PydField(
        default=None, ge=1, description="ID пользователя, закрывшего сессию."
    )
    sort_orders: Optional[List[SortOrder]] = PydField(
        default=None, description="Список правил сортировки."
    )
    limit: Optional[int] = PydField(
        default=None, ge=1, le=10000, description="Количество записей в выдаче."
    )
    offset: Optional[int] = PydField(
        default=None, ge=0, description="Смещение для пагинации."
    )

    @model_validator(mode="after")
    def _validate_dates(cls, values: "DocCashSessionGetRequest"):
        if (
            values.start_date
            and values.end_date
            and values.end_date < values.start_date
        ):
            raise ValueError("end_date не может быть меньше start_date")
        return values


__all__ = [
    "DocCashSession",
    "DocCashSessionGetRequest",
    "DocCashSessionSortColumn",
    "SortDirection",
    "SortOrder",
]
