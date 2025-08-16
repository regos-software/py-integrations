
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Counts(BaseModel):
    sale_count: Optional[int] = None
    return_count: Optional[int] = None
    debt_amount: Optional[Decimal] = None          # Сумма выданного в долг (по платежам)
    debt_paid_amount: Optional[Decimal] = None     # Сумма оплаченного долга (по товару)
    gross_profit: Optional[Decimal] = None         # Валовая прибыль



class CountsGetRequest(BaseModel):
    """
    Параметры запроса для /v1/RetailReport/Counts
    start_date и end_date — обязательны (Unix time, сек).
    operating_cash_ids — необязательный массив ID касс.
    """
    start_date: int
    end_date: int
    operating_cash_ids: Optional[List[int]] = None
