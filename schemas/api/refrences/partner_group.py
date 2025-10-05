from __future__ import annotations

from pydantic import BaseModel


class PartnerGroup(BaseModel):
    """
    Группа контрагентов.
    """
    id: int
    parent_id: int
    name: str
    child_count: int
    last_update: int  # unixtime (sec)
