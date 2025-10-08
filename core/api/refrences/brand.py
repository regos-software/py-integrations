from typing import List, Optional, Iterable
from enum import Enum
from pydantic import BaseModel

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.brand import Brand

logger = setup_logger("references.brand")

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

class BrandGetRequest(BaseModel):
    ids: Optional[List[int]] = None
    sort_orders: Optional[List[SortOrder]] = None
    search: Optional[str] = None
    limit: Optional[int] = 10000
    offset: Optional[int] = 0

class BrandAddRequest(BaseModel):
    name: str

class BrandEditRequest(BaseModel):
    id: int
    name: str

class BrandDeleteRequest(BaseModel):
    id: int

class BrandService:
    PATH_GET = "Brand/Get"
    PATH_ADD = "Brand/Add"
    PATH_EDIT = "Brand/Edit"
    PATH_DELETE = "Brand/Delete"

    def __init__(self, api):
        self.api = api

    async def get(self, req: BrandGetRequest) -> List[Brand]:
        """
        POST …/v1/Brand/Get
        Возвращает массив брендов.
        """
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
           return []
        return [Brand.model_validate(x) for x in resp.result]

    async def get_by_ids(self, ids: Iterable[int]) -> List[Brand]:
        return await self.get(BrandGetRequest(ids=list(ids)))

    async def add(self, req: BrandAddRequest) -> int | None:
        """
        POST …/v1/Brand/Add
        Создаёт новый бренд.
        Возвращает id созданного бренда.
        """
        resp = await self.api.call(self.PATH_ADD, req, APIBaseResponse)
        if not getattr(resp, "ok", False):
          return None
        return resp.result

    async def edit(self, req: BrandEditRequest) -> bool:
        """
        POST …/v1/Brand/Edit
        Редактирует существующий бренд по id.
        Возвращает True при успехе, False при ошибке.
        """
        resp = await self.api.call(self.PATH_EDIT, req, APIBaseResponse)
        return getattr(resp, "ok", False)

    async def delete(self, req: BrandDeleteRequest) -> bool:
        """
        POST …/v1/Brand/Delete
        Удаляет бренд по id.
        Возвращает True при успехе, False при ошибке.
        """
        resp = await self.api.call(self.PATH_DELETE, req, APIBaseResponse)
        return getattr(resp, "ok", False)

