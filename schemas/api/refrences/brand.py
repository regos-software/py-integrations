from __future__ import annotations
from typing import Optional

from pydantic import BaseModel


class Brand(BaseModel):
    id: int
    name: Optional[str] = None
    last_update: int