from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel

from schemas.api.base import APIBaseResponse


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


class ItemGroupGetRequest(BaseModel):
    """
    Параметры для /v1/ItemGroup/Get
    """

    ids: Optional[List[int]] = None  # Список ID групп для фильтрации
    parent_ids: Optional[List[int]] = (
        None  # Список ID родительских групп для фильтрации
    )
    name: Optional[str] = None  # Фильтр по наименованию группы (частичное совпадение)
