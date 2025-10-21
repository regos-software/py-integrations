from pydantic import BaseModel


class RetailReturnReason(BaseModel):
    id: int
    name: str
    description: str
    enabled: bool
    last_update: int
