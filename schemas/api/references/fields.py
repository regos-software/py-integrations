# schemas/api/common/fields.py
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field as PydField, field_validator


# ---------- Справочники ----------


class EntityType(str, Enum):
    """
    Сущность, к которой привязано доп. поле.
    Расширяйте по мере добавления новых сущностей.
    """

    RetailCustomer = "RetailCustomer"
    Partner = "Partner"
    DocPurchase = "DocPurchase"


class FieldDataType(str, Enum):
    """
    Тип данных значения доп. поля.
    """

    string = "string"
    int = "int"
    decimal = "decimal"
    bool = "bool"


# ---------- Метамодель доп. поля ----------


class Field(BaseModel):
    """
    Дополнительное (кастомное) поле, привязанное к сущности.
    Содержит метаданные: ключ, название, тип, обязательность и пр.
    """

    id: int
    key: str  # machine-name, уникальный
    name: str  # человекочитаемое имя
    entity_type: EntityType
    data_type: FieldDataType
    is_custom: bool
    required: bool

    # Нормализация входных строк к валидным enum (на случай разных регистров)
    @field_validator("entity_type", "data_type", mode="before")
    @classmethod
    def _enum_normalize(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


# ---------- Значения доп. полей, используемые в моделях сущностей ----------


class FieldValue(BaseModel):
    """
    Значение доп. поля в объекте сущности (рид-модель).
    В сущности хранится массив FieldValue[].
    value — всегда строка; сервер/клиент приводит к типу из data_type.
    """

    key: str
    name: str
    data_type: FieldDataType
    value: str = PydField(..., description="Строковое представление значения")

    @field_validator("data_type", mode="before")
    @classmethod
    def _normalize_dt(cls, v):
        return v.strip() if isinstance(v, str) else v


class FieldValueAdd(BaseModel):
    """
    Модель для передачи значения доп. поля при создании сущности.
    Передаётся массив FieldValueAdd[]. Обязательность определяется метаданными (required).
    """

    key: str
    value: str = PydField(..., description="Строковое представление значения")


class FieldValueEdit(BaseModel):
    """
    Модель для редактирования значения доп. поля.
    Передаётся массив FieldValueEdit[].
    - deleted = true  — удалить значение поля у сущности (value игнорируется)
    - deleted = false — оставить/обновить значение (value можно не передавать, если не меняется)
    """

    key: str
    value: Optional[str] = None
    deleted: bool = False


# ---------- Псевдонимы для удобства аннотаций ----------

FieldValues = List[FieldValue]
FieldValueAdds = List[FieldValueAdd]
FieldValueEdits = List[FieldValueEdit]
"""
Массивы моделей значений доп. полей.
Используются в моделях сущностей для операций добавления/редактирования.
Пример:
  - fields: Optional[FieldValueAdds] = None
  - fields: Optional[FieldValueEdits] = None
  - fields: Optional[FieldValues] = None"""
