from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ItemGroup(BaseModel):
    """
    Модель, описывающая группы номенклатуры.
    """
    id: Optional[int] = None  # ID группы в системе
    parent_id: Optional[int] = None  # ID родительской группы
    path: Optional[str] = None  # Путь к группе (вложенные группы через '/')
    name: Optional[str] = None  # Наименование группы
    child_count: Optional[int] = None  # Количество дочерних групп
    last_update: Optional[int] = None  # Дата последнего изменения (unixtime, сек)
