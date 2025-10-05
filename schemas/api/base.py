# schemas/api/base.py
from typing import Optional, Any
from pydantic import BaseModel, Field

class APIBaseResponse(BaseModel):
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

class APIErrorResult(BaseModel):
    error: int
    description: str

class ArrayResult(BaseModel):
    row_affected: int
    ids: list[int]
