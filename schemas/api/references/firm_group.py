from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FirmGroup(BaseModel):
    """
    Модель, описывающая группы предприятий.
    """

    id: int  # ID группы
    parent_id: Optional[int] = None  # ID родительской группы
    name: str  # Наименование группы
    child_count: int  # Количество дочерних групп
    last_update: int  # Дата последнего изменения (unixtime, сек)
