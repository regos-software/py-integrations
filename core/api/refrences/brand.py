from typing import List, Iterable
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.brand import Brand

logger = setup_logger("brand")

class BrandColumn(str, Enum):
    Id = "Id"
    Name = "Name"
    LastUpdate = "LastUpdate"


class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"

class SortOrder(BaseModel):
    column: BrandColumn
    direction: SortDirection

class BrandService:
    PATH_GET = "References/Brand/Get"
    PATH_ADD = "References/Brand/Add"
    PATH_EDIT = "References/Brand/Edit"
    PATH_DELETE = "References/Brand/Delete"

    def __init__(self, api):
        self.api = api

