"""Схемы документов инвентаризации."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, model_validator

from schemas.api.base import APIBaseResponse, ArrayResult, BaseSchema
from schemas.api.rbac.user import User
from schemas.api.references.price_type import PriceType
from schemas.api.references.stock import Stock


class InventoryCompareType(int, Enum):
    """Допустимые значения сопоставления инвентаризации."""

    OPEN_DATE = 1
    CLOSE_DATE = 2
    OPERATION_DATE = 3


class DocInventory(BaseSchema):
    """Рид-модель документа инвентаризации."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="ID документа инвентаризации.")
    code: str = PydField(..., description="Код документа.")
    open_date: Optional[int] = PydField(
        default=None, ge=0, description="Дата открытия инвентаризации (Unix)."
    )
    close_date: Optional[int] = PydField(
        default=None, ge=0, description="Дата закрытия инвентаризации (Unix)."
    )
    compare_type: Optional[InventoryCompareType] = PydField(
        default=None, description="Тип сопоставления документа."
    )
    stock: Optional[Stock] = PydField(default=None, description="Склад документа.")
    description: Optional[str] = PydField(
        default=None, description="Дополнительное описание."
    )
    attached_user: Optional[User] = PydField(
        default=None, description="Ответственный пользователь."
    )
    price_type: Optional[PriceType] = PydField(
        default=None, description="Тип цены для операций."
    )
    blocked: Optional[bool] = PydField(
        default=None, description="Флаг блокировки документа."
    )
    closed: Optional[bool] = PydField(
        default=None, description="Флаг закрытия документа."
    )
    full: Optional[bool] = PydField(
        default=None, description="Признак полной инвентаризации."
    )
    create_docinout: Optional[bool] = PydField(
        default=None,
        description="Создавать документы списания/занесения при закрытии.",
    )
    external_id: Optional[str] = PydField(
        default=None, description="Внешний идентификатор документа."
    )
    current_user_blocked: Optional[bool] = PydField(
        default=None,
        description="Документ заблокирован текущим пользователем.",
    )
    deleted_mark: Optional[bool] = PydField(
        default=None, description="Документ помечен на удаление."
    )
    last_update: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Метка последнего изменения (Unix).",
    )


class DocInventorySortOrder(BaseSchema):
    """Правило сортировки документов инвентаризации."""

    model_config = ConfigDict(extra="forbid")

    column: Optional[str] = PydField(
        default=None,
        description=(
            "Поле сортировки: Id, Code, OpenDate, CloseDate, CompareType, "
            "StockName, AttacheUserName, Blocked, Closed, DeletedMark, LastUpdate."
        ),
    )
    direction: Optional[str] = PydField(
        default=None, description="Направление сортировки (ASC|DESC)."
    )


class DocInventoryGetRequest(BaseSchema):
    """Фильтры получения документов инвентаризации."""

    model_config = ConfigDict(extra="forbid")

    compare_type: Optional[InventoryCompareType] = PydField(
        default=None, description="Тип сопоставления документа."
    )
    ids: Optional[List[int]] = PydField(
        default=None, description="Список ID документов инвентаризации."
    )
    stock_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID складов."
    )
    attached_user_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID ответственных пользователей."
    )
    start_date: Optional[int] = PydField(
        default=None, ge=0, description="Начало периода (Unix)."
    )
    end_date: Optional[int] = PydField(
        default=None, ge=0, description="Конец периода (Unix)."
    )
    closed: Optional[bool] = PydField(
        default=None, description="Фильтр по закрытым документам."
    )
    blocked: Optional[bool] = PydField(
        default=None, description="Фильтр по заблокированным документам."
    )
    deleted_mark: Optional[bool] = PydField(
        default=None, description="Фильтр по пометке удаления."
    )
    search: Optional[str] = PydField(
        default=None,
        description="Поиск по коду, фирме, ИНН, складу или ответственному.",
    )
    sort_orders: Optional[List[DocInventorySortOrder]] = PydField(
        default=None, description="Набор правил сортировки."
    )
    limit: Optional[int] = PydField(
        default=None, ge=1, description="Количество записей в выдаче."
    )
    offset: Optional[int] = PydField(
        default=None, ge=0, description="Смещение для пагинации."
    )

    @model_validator(mode="after")
    def _validate_dates(cls, values: "DocInventoryGetRequest"):
        if (
            values.start_date
            and values.end_date
            and values.end_date < values.start_date
        ):
            raise ValueError("end_date не может быть меньше start_date")
        return values


class DocInventoryAddRequest(BaseSchema):
    """Параметры создания документа инвентаризации."""

    model_config = ConfigDict(extra="forbid")

    open_date: int = PydField(..., ge=0, description="Дата открытия (Unix).")
    compare_type: InventoryCompareType = PydField(
        ..., description="Тип сопоставления документа."
    )
    stock_id: int = PydField(..., ge=1, description="ID склада.")
    price_type_id: int = PydField(..., ge=1, description="ID вида цены.")
    attached_user_id: int = PydField(..., ge=1, description="ID ответственного.")
    description: Optional[str] = PydField(
        default=None, description="Дополнительное описание."
    )
    full: bool = PydField(default=True, description="Признак полной инвентаризации.")
    create_docinout: bool = PydField(
        default=True,
        description=(
            "Создавать документы списания/занесения при закрытии инвентаризации."
        ),
    )
    external_id: Optional[str] = PydField(
        default=None, description="Внешний идентификатор документа."
    )


class DocInventoryEditRequest(BaseSchema):
    """Параметры изменения документа инвентаризации."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID документа инвентаризации.")
    open_date: Optional[int] = PydField(
        default=None, ge=0, description="Дата открытия (Unix)."
    )
    compare_type: Optional[InventoryCompareType] = PydField(
        default=None, description="Тип сопоставления документа."
    )
    stock_id: Optional[int] = PydField(default=None, ge=1, description="ID склада.")
    price_type_id: Optional[int] = PydField(
        default=None, ge=1, description="ID вида цены."
    )
    description: Optional[str] = PydField(
        default=None, description="Дополнительное описание."
    )
    full: Optional[bool] = PydField(
        default=None, description="Признак полной инвентаризации."
    )
    create_docinout: Optional[bool] = PydField(
        default=None,
        description=(
            "Создавать документы списания/занесения при закрытии инвентаризации."
        ),
    )
    external_id: Optional[str] = PydField(
        default=None, description="Внешний идентификатор документа."
    )
    attached_user_id: Optional[int] = PydField(
        default=None, ge=1, description="ID ответственного пользователя."
    )


class DocInventoryAddResult(BaseSchema):
    """Результат создания документа инвентаризации."""

    model_config = ConfigDict(extra="ignore")

    new_id: int = PydField(..., ge=1, description="ID созданного документа.")


class DocInventoryGetResponse(APIBaseResponse[List[DocInventory]]):
    """Ответ на запрос /v1/DocInventory/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "DocInventory",
    "DocInventoryAddRequest",
    "DocInventoryAddResult",
    "DocInventoryEditRequest",
    "DocInventoryGetRequest",
    "DocInventoryGetResponse",
    "DocInventorySortOrder",
    "InventoryCompareType",
]
