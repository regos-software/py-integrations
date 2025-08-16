from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class CashAmountDetails(BaseModel):
    current_amount: Optional[Decimal] = None
    start_amount: Optional[Decimal] = None
    income: Optional[Decimal] = None
    outcome: Optional[Decimal] = None
    end_amount: Optional[Decimal] = None

class CashAmountDetailsGetRequest(BaseModel):
    """
    Параметры запроса для /v1/CashOperation/GetAmountDetails
    start_date и end_date — обязательны (Unix time, сек).
    operating_cash_id — необязательный.
    """
    start_date: int
    end_date: int
    operating_cash_id: Optional[int] = None