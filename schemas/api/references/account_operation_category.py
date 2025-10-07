from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class AccountOperationCategory(BaseModel):
    id: int                                     # ID статьи дохода или расхода
    parent_id: Optional[int] = None             # ID родительской статьи дохода или расхода
    child_count: int                            # Количество вложенных (дочерних) статей дохода/расхода
    name: str                                   # Наименование статьи
    positive: bool                              # Вид статьи: True — доход, False — расход
    last_update: int                            # Дата последнего изменения (Unix time)
