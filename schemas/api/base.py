from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel, Field


class APIBaseResponse(BaseModel):
    """
    Универсальный ответ API REGOS.
    """
    ok: bool = Field(..., description="True/False – метка успешного ответа")
    result: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        None, description="Объект или массив объектов, возвращаемый сервером"
    )

class APIErrorResult(BaseModel):
    """
    Модель описания ошибки в ответе сервера.
    """
    error: int = Field(..., description="Код ошибки")
    description: str = Field(..., description="Описание ошибки")


class ArrayResult(BaseModel):
    """
    Универсальный ответ API REGOS при массовом действии.
    """
    row_affected: int
    ids: List[int]
