from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


# ---------- SortOrders ----------


class SortDirection(str, Enum):
    """
    Порядок сортировки:
      - asc  — по возрастанию
      - desc — по убыванию
    """

    asc = "asc"
    desc = "desc"


class SortOrder(BaseModel):
    """
    Элемент массива сортировки.
    Важно: набор допустимых значений column определяется конкретной моделью
    (например: id, name, code, last_update и т. п.). При передаче недопустимого
    значения сервер должен вернуть ошибку валидации.
    """

    column: str = Field(
        ..., description="Имя сортируемого поля (см. документацию конкретной модели)."
    )
    direction: SortDirection = Field(
        SortDirection.asc, description="Порядок сортировки."
    )

    # Принимаем 'ASC'/'DESC' и т. п. — нормализуем в нижний регистр.
    @field_validator("direction", mode="before")
    @classmethod
    def _normalize_direction(cls, v):
        if isinstance(v, str):
            v_low = v.strip().lower()
            if v_low in {"asc", "desc"}:
                return v_low
        return v


# Удобный псевдоним для поля в запросах
# sort_orders: Optional[SortOrders] = None
SortOrders = List[SortOrder]
"""
Массив элементов сортировки.
Сортировка выполняется по порядку элементов массива.
Например:
  - [ { column: "name", direction: "asc" },
      { column: "id",   direction: "desc" } ]
  - сначала сортирует по name по возрастанию,
  - при равенстве name — по id по убыванию.
"""
