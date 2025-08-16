
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from schemas.api.docs.cash_operation_type import CashOperationType



class CashOperation(BaseModel):
    id: Optional[int] = None
    date: Optional[int] = None  # Unix time (sec)
    type: Optional[CashOperationType] = None
    payment_type_id: Optional[int] = None
    payment_type_name: Optional[str] = None
    session_uuid: Optional[str] = None
    document_uuid: Optional[str] = None
    operating_cash_id: Optional[int] = None
    value: Optional[Decimal] = None
    description: Optional[str] = None
    user_id: Optional[int] = None
    user_full_name: Optional[str] = None
    last_update: Optional[int] = None  # Unix time (sec)


class CashOperationGetRequest(BaseModel):
    """
    Параметры запроса для /v1/CashOperation/Get

    start_date: обязательный (Unix time, сек)
    end_date:   обязательный (Unix time, сек)
    operating_cash_id: необязательный (ID кассы)
    limit:      необязательный (количество элементов)
    offset:     необязательный (смещение)
    """
    start_date: int
    end_date: int
    operating_cash_id: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None