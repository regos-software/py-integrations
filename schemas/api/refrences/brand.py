from __future__ import annotations

from pydantic import BaseModel


class Currency(BaseModel):
    id: int
    name: str
    last_update: int