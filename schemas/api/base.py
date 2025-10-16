# schemas/api/base.py
from decimal import Decimal
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: float})


T = TypeVar("T", default=Any)


class APIBaseResponse(BaseSchema, Generic[T]):
    """
    Универсальный ответ API REGOS.
    Разные методы возвращают разные формы result (dict, list[dict], list[int], int, str ...),
    поэтому здесь допускаем любой тип.
    """

    ok: bool = Field(..., description="True/False – метка успешного ответа")
    result: Optional[T] = Field(
        default=None,
        description="Данные ответа (могут быть dict, list[dict], list[int], и т.д.)",
    )
    next_offset: Optional[int] = None
    total: Optional[int] = None


class APIErrorResult(BaseSchema):
    error: int
    description: str


class ArrayResult(BaseSchema):
    row_affected: int
    ids: list[int]


class IDRequest(BaseSchema):
    id: int
