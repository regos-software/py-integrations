# schemas/api/references/retail_customer.py
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, List, Optional

from pydantic import Field as PydField, EmailStr, field_validator
from pydantic.config import ConfigDict

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.common.filters import Filters
from schemas.api.common.sort_orders import SortOrders
from schemas.api.references.fields import FieldValueAdds, FieldValueEdits, FieldValues
from schemas.api.references.region import Region
from schemas.api.references.retail_customer_group import RetailCustomerGroup


# ---------- Вспомогательные модели ----------


class Sex(str, Enum):
    """
    Пол покупателя:
      - non    — Не указан
      - male   — Мужской
      - female — Женский
    """

    non = "non"
    male = "male"
    female = "female"


# ---------- Основная модель ----------


class RetailCustomer(BaseSchema):
    """
    Покупатель (физ. лицо розницы).
    """

    # Настраиваем приём лишних полей на чтении мягко (если нужно — можно запретить)
    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID покупателя.")
    region: Optional[Region] = PydField(None, description="Регион проживания (Region).")
    group: RetailCustomerGroup = PydField(
        ..., description="Группа покупателя (RetailCustomerGroup)."
    )

    last_purchase: Optional[int] = PydField(
        None, description="ID последней покупки (если ведётся)."
    )
    debt: Optional[Decimal] = PydField(None, description="Долг покупателя.")

    # Персональные данные
    first_name: Optional[str] = PydField(None, description="Имя.")
    last_name: Optional[str] = PydField(None, description="Фамилия.")
    middle_name: Optional[str] = PydField(None, description="Отчество.")
    full_name: Optional[str] = PydField(None, description="Полное ФИО.")
    sex: Sex = PydField(Sex.non, description="Пол: non|male|female.")
    date_of_birth: Optional[str] = PydField(
        None, description="Дата рождения (строка, напр. YYYY-MM-DD)."
    )

    # Контакты и адрес
    address: Optional[str] = PydField(None, description="Адрес.")
    main_phone: Optional[str] = PydField(None, description="Основной телефон.")
    phones: Optional[str] = PydField(
        None, description="Доп. телефоны (свободный формат)."
    )
    email: Optional[str] = PydField(None, description="E-mail.")

    # Реферальная информация
    refer_id: Optional[int] = PydField(None, description="ID реферального покупателя.")

    # Доп. поля и заметки
    fields: Optional[FieldValues] = PydField(
        None, description="Массив значений доп. полей (FieldValue[])."
    )
    description: Optional[str] = PydField(None, description="Примечание/заметка.")

    # Служебные флаги и метаданные
    deleted_mark: bool = PydField(..., description="Метка удаления: true/false.")
    last_update: int = PydField(
        ..., description="Unix time (сек) последнего изменения."
    )

    # легкая нормализация пробелов на чтении
    @field_validator(
        "first_name",
        "last_name",
        "middle_name",
        "full_name",
        "address",
        "main_phone",
        "phones",
        "email",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("sex", mode="before")
    @classmethod
    def _normalize_sex(cls, v):
        if v is None or isinstance(v, Sex):
            return v
        if isinstance(v, str):
            s = v.strip().lower()
            if s == "none":
                return Sex.non
            if s in {"male", "female"}:
                return Sex(s)
        raise ValueError("sex должен быть одним из: none | male | female")


# ---------- Get ----------


class RetailCustomerGetRequest(BaseSchema):
    # запретим опечатки во входе
    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = None
    group_ids: Optional[List[int]] = None
    region_ids: Optional[List[int]] = None
    refer_ids: Optional[List[int]] = None

    sex: Optional[Sex] = None

    sort_orders: Optional[SortOrders] = None
    filters: Optional[Filters] = None

    search: Optional[str] = None
    main_phone: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class RetailCustomerGetResponse(
    APIBaseResponse[List[RetailCustomer] | dict[str, Any]]
):
    """Response model for RetailCustomer/Get."""


# ---------- Add ----------


class RetailCustomerAddRequest(BaseSchema):
    """
    Параметры для /v1/RetailCustomer/Add
    """

    model_config = ConfigDict(extra="forbid")

    group_id: int = PydField(..., ge=1, description="ID группы покупателя.")
    region_id: Optional[int] = PydField(
        None, ge=1, description="ID региона (опционально)."
    )

    first_name: str = PydField(..., description="Имя.")
    last_name: Optional[str] = PydField(None, description="Фамилия.")
    middle_name: Optional[str] = PydField(None, description="Отчество.")
    full_name: Optional[str] = PydField(None, description="Полное ФИО.")

    # только non|male|female
    sex: Optional[Sex] = PydField(None, description="Пол: non|male|female.")
    date_of_birth: Optional[str] = PydField(
        None, description="Дата рождения (строка, напр. YYYY-MM-DD)."
    )

    address: Optional[str] = PydField(None, description="Адрес.")
    main_phone: Optional[str] = PydField(None, description="Основной телефон.")
    phones: Optional[str] = PydField(None, description="Доп. телефоны.")
    # Строже на вход в Add/Edit, при чтении в модели — обычная строка
    email: Optional[EmailStr] = PydField(None, description="E-mail.")

    refer_id: Optional[int] = PydField(None, ge=1, description="ID реферала.")
    description: Optional[str] = PydField(None, description="Примечание.")

    fields: Optional[FieldValueAdds] = PydField(
        None, description="Массив FieldValueAdd[]."
    )

    @field_validator(
        "first_name",
        "last_name",
        "middle_name",
        "full_name",
        "address",
        "main_phone",
        "phones",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("sex", mode="before")
    @classmethod
    def _normalize_sex(cls, v):
        if v is None or isinstance(v, Sex):
            return v
        if isinstance(v, str):
            s = v.strip().lower()
            if s == "none":
                return Sex.non
            if s in {"male", "female"}:
                return Sex(s)
        raise ValueError("sex должен быть одним из: none | male | female")


# ---------- Edit ----------


class RetailCustomerEditRequest(BaseSchema):
    """
    Параметры для /v1/RetailCustomer/Edit
    """

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID покупателя.")

    group_id: Optional[int] = PydField(None, ge=1, description="ID группы.")
    region_id: Optional[int] = PydField(None, ge=1, description="ID региона.")

    first_name: Optional[str] = PydField(None, description="Имя.")
    last_name: Optional[str] = PydField(None, description="Фамилия.")
    middle_name: Optional[str] = PydField(None, description="Отчество.")
    full_name: Optional[str] = PydField(None, description="Полное ФИО.")

    # только non|male|female
    sex: Optional[Sex] = PydField(None, description="Пол: non|male|female.")
    date_of_birth: Optional[str] = PydField(
        None, description="Дата рождения (строка, напр. YYYY-MM-DD)."
    )

    address: Optional[str] = PydField(None, description="Адрес.")
    main_phone: Optional[str] = PydField(None, description="Основной телефон.")
    phones: Optional[str] = PydField(None, description="Доп. телефоны.")
    email: Optional[EmailStr] = PydField(None, description="E-mail.")

    refer_id: Optional[int] = PydField(None, ge=1, description="ID реферала.")
    description: Optional[str] = PydField(None, description="Примечание.")

    fields: Optional[FieldValueEdits] = PydField(
        None, description="Массив FieldValueEdit[]."
    )

    @field_validator(
        "first_name",
        "last_name",
        "middle_name",
        "full_name",
        "address",
        "main_phone",
        "phones",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("sex", mode="before")
    @classmethod
    def _normalize_sex(cls, v):
        if v is None or isinstance(v, Sex):
            return v
        if isinstance(v, str):
            s = v.strip().lower()
            if s == "none":
                return Sex.non
            if s in {"male", "female"}:
                return Sex(s)
        raise ValueError("sex должен быть одним из: none | male | female")


# ---------- DeleteMark ----------


class RetailCustomerDeleteMarkRequest(BaseSchema):
    """
    Параметры для /v1/RetailCustomer/DeleteMark
    """

    model_config = ConfigDict(extra="forbid")
    id: int = PydField(..., ge=1, description="ID покупателя.")


# ---------- Delete ----------


class RetailCustomerDeleteRequest(BaseSchema):
    """
    Параметры для /v1/RetailCustomer/Delete
    """

    model_config = ConfigDict(extra="forbid")
    id: int = PydField(..., ge=1, description="ID покупателя.")


__all__ = [
    "Sex",
    "RetailCustomer",
    "RetailCustomerGetRequest",
    "RetailCustomerGetResponse",
    "RetailCustomerAddRequest",
    "RetailCustomerEditRequest",
    "RetailCustomerDeleteMarkRequest",
    "RetailCustomerDeleteRequest",
]
