from typing import Optional

from pydantic import BaseModel


class CashOperationType(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
