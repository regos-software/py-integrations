from pydantic import BaseModel


class RetailReturnReason(BaseModel):
    id: int
    name: str
    description: Optional[str]
    enabled: bool
    last_update: int
