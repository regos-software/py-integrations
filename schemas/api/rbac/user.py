from typing import Optional
from pydantic import BaseModel


class UserGroup(BaseModel):
    id: int
    parent_id: Optional[int] = None
    name: str
    child_count: int
    last_update: int


class User(BaseModel):
    id: int
    full_name: Optional[str] = None
    main_phone: Optional[str] = None
    user_group: Optional[UserGroup] = None
    enable_hints: Optional[bool] = None
    system: Optional[bool] = None
    seller_barcode: Optional[str] = None
    last_update: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    sex: str = "none"  
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    phones: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    login: Optional[str] = None
    can_authorize: Optional[bool] = None
    active: Optional[bool] = None
    language_code: Optional[str] = None
