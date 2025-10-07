from __future__ import annotations

from pydantic import BaseModel


class Color(BaseModel):
    id: int
    name: str
    last_update: int