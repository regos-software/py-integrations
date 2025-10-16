# schemas/api/common/filters.py
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class FilterOperator(str, Enum):
    """
    Допустимые операторы:
      - Equal (=), NotEqual (!=), Greater (>), Less (<),
        GreaterOrEqual (>=), LessOrEqual (<=), Like, Exists, NotExists
    """

    Equal = "Equal"
    NotEqual = "NotEqual"
    Greater = "Greater"
    Less = "Less"
    GreaterOrEqual = "GreaterOrEqual"
    LessOrEqual = "LessOrEqual"
    Like = "Like"
    Exists = "Exists"
    NotExists = "NotExists"


class Filter(BaseModel):
    """
    Универсальный фильтр для выборок.

    Правила (валидация типов/применимости операторов — на стороне сервера):
      - value — строка, соответствующая типу данных поля:
          * string  — произвольная строка
          * int     — целое в текстовом представлении
          * decimal — десятичное число в текстовом представлении
          * bool    — 'true' | 'false' (регистронезависимо)
      - Exists/NotExists не требуют value (игнорируется).
    """

    field: str = Field(
        ..., description="Имя поля (например: first_name, region_id, date_of_birth)."
    )
    operator: FilterOperator
    value: Optional[str] = Field(
        None,
        description="Значение фильтра (строкой). Для Exists/NotExists не требуется.",
    )

    @model_validator(mode="after")
    def _check_value_presence(self):
        if self.operator in {FilterOperator.Exists, FilterOperator.NotExists}:
            return self
        if self.value is None or str(self.value).strip() == "":
            raise ValueError(
                "Для выбранного оператора требуется непустое значение 'value'."
            )
        return self


Filters = List[Filter]
