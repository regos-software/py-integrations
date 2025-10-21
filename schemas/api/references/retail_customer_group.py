from typing import Optional
from pydantic import BaseModel


class RetailCustomerGroup(BaseModel):
    """
    Группа покупателей.
    """

    id: int
    parent_id: Optional[int] = None
    name: str
    last_update: int  # unixtime (sec)
    child_count: Optional[int] = None  # количество дочерних групп
