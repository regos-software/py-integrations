# schemas/api/base.py
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        json_encoders={Decimal: float}
    )

class APIBaseResponse(BaseSchema):
    """
    Универсальный ответ API REGOS.
    Разные методы возвращают разные формы result (dict, list[dict], list[int], int, str ...),
    поэтому здесь допускаем любой тип.
    """
    ok: bool = Field(..., description="True/False – метка успешного ответа")
    result: Optional[Any] = Field(
        default=None,
        description="Данные ответа (могут быть dict, list[dict], list[int], и т.д.)"
    )

class APIErrorResult(BaseSchema):
    error: int
    description: str

class ArrayResult(BaseSchema):
    row_affected: int
    ids: list[int]
