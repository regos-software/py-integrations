from typing import Optional
from pydantic import BaseModel


class Region(BaseModel):
    """
    Регион.
    """

    id: int
    parent_id: Optional[int] = None
    name: str
    last_update: int  # unixtime (sec)
