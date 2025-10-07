from typing import List, Optional, Iterable
from enum import Enum
from pydantic import BaseModel

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.account_operation_category import AccountOperationCategory

logger = setup_logger("references.account_operation_category")


class SortColumn(str, Enum):
    ID = "Id"                     # ID статьи
    PARENT_ID = "ParentId"        # ID родительской статьи
    CHILD_COUNT = "ChildCount"    # Кол-во дочерних статей
    NAME = "Name"                 # Наименование
    POSITIVE = "Positive"         # Влияние на счёт
    LAST_UPDATE = "LastUpdate"    # Дата изменения


class SortDirection(str, Enum):
    ASC = "asc"             # По возрастанию
    DESC = "desc"           # По убыванию


class SortOrder(BaseModel):
    column: SortColumn
    direction: SortDirection


class AccountOperationCategoryGetRequest(BaseModel):
    ids: Optional[List[int]] = None                   # Массив ID статей
    parent_ids: Optional[List[int]] = None            # Массив ID родительских ???
    child_count: Optional[int] = None                 # Количество дочерних статей
    positive: bool                                    # Вид статьи: True — доход, False — расход
    sort_orders: Optional[List[SortOrder]] = None     # Сортировка
    search: Optional[str] = None                      # Поиск по имени
    limit: Optional[int] = 10000
    offset: Optional[int] = 0


class AccountOperationCategoryAddRequest(BaseModel):
    parent_id: Optional[int] = 0                      # ID родителя, если нет — 0
    name: str                                         # Наименование
    positive: bool                                    # Вид статьи: True — доход, False — расход


class AccountOperationCategoryEditRequest(BaseModel):
    id: int                                           # ID статьи
    parent_id: Optional[int] = None                   # ID родителя
    name: Optional[str] = None                        # Новое наименование


class AccountOperationCategoryDeleteRequest(BaseModel):
    id: int                                           # ID статьи


class AccountOperationCategoryService:
    PATH_GET = "AccountOperationCategory/Get"
    PATH_ADD = "AccountOperationCategory/Add"
    PATH_EDIT = "AccountOperationCategory/Edit"
    PATH_DELETE = "AccountOperationCategory/Delete"

    def __init__(self, api):
        self.api = api

    async def get(self, req: AccountOperationCategoryGetRequest) -> List[AccountOperationCategory]:
        """
        POST …/v1/AccountOperationCategory/Get
        Возвращает список статей доходов/расходов.
        """
        resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
        if not getattr(resp, "ok", False) or not isinstance(resp.result, list):
            return []
        return [AccountOperationCategory.model_validate(x) for x in resp.result]

    async def get_by_ids(self, ids: Iterable[int], positive: bool) -> List[AccountOperationCategory]:
        return await self.get(AccountOperationCategoryGetRequest(ids=list(ids), positive=positive))

    async def add(self, req: AccountOperationCategoryAddRequest) -> int | None:
        """
        POST …/v1/AccountOperationCategory/Add
        Создаёт новую статью дохода/расхода.
        """
        resp = await self.api.call(self.PATH_ADD, req, APIBaseResponse)
        if not getattr(resp, "ok", False):
            return None
        return resp.result

    async def edit(self, req: AccountOperationCategoryEditRequest) -> bool:
        """
        POST …/v1/AccountOperationCategory/Edit
        Редактирует статью дохода/расхода.
        """
        resp = await self.api.call(self.PATH_EDIT, req, APIBaseResponse)
        return getattr(resp, "ok", False)

    async def delete(self, req: AccountOperationCategoryDeleteRequest) -> bool:
        """
        POST …/v1/AccountOperationCategory/Delete
        Удаляет статью дохода/расхода по ID.
        """
        resp = await self.api.call(self.PATH_DELETE, req, APIBaseResponse)
        return getattr(resp, "ok", False)
