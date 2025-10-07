from typing import List, Optional, Iterable
from enum import Enum
from pydantic import BaseModel

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.color import Color

logger = setup_logger("references.color")

class SortColumn(str, Enum):
    ID = "Id"
    NAME = "Name"
    LAST_UPDATE = "LastUpdate"

class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SortOrder(BaseModel):
    column: SortColumn
    direction: SortDirection

class ColorGetRequest(BaseModel):
    ids: Optional[List[int]] = None                   #Массив id цветов
    sort_orders: Optional[List[SortOrder]] = None     #Сортировака выходных параметров
    search: Optional[str] = None                      #Строка поиска по полю name
    limit: Optional[int] = 10000
    offset: Optional[int] = 0

class ColorAddRequest(BaseModel):
    name: str

class ColorEditRequest(BaseModel):
    id: int
    name: Optional[str] = None

class ColorDeleteRequest(BaseModel):
    id: int

class ColorService:
    PATH_GET = "Color/Get"
    PATH_ADD = "Color/Add"
    PATH_EDIT = "Color/Edit"
    PATH_DELETE = "Color/Delete"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ColorGetRequest) -> List[Color]:
        """
        POST …/v1/Color/Get
        Возвращает массив цветов.
        """
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [Color.model_validate(x) for x in resp.result]

    async def get_by_ids(self, ids: Iterable[int]) -> List[Color]:
        return await self.get(ColorGetRequest(ids=list(ids)))

    async def add(self, req: ColorAddRequest) -> int | None:
        """
        POST …/v1/Color/Add
        Создаёт новый цвет.
        Возвращает id созданного цвета.
        """
        resp = await self.api.call(self.PATH_ADD, req, APIBaseResponse)
        if not getattr(resp, "ok", False):
            return None
        return resp.result

    async def edit(self, req: ColorEditRequest) -> bool:
        """
        POST …/v1/Color/Edit
        Редактирует существующий цвет по id.
        """
        resp = await self.api.call(self.PATH_EDIT, req, APIBaseResponse)
        return getattr(resp, "ok", False)

    async def delete(self, req: ColorDeleteRequest) -> bool:
        """
        POST …/v1/Color/Delete
        Удаляет цвет по id.
        """
        resp = await self.api.call(self.PATH_DELETE, req, APIBaseResponse)
        return getattr(resp, "ok", False)
