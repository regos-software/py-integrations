
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class Payment(BaseModel):
    """Модель суммы продаж/возвратов по форме оплаты."""
    payment_type_name: Optional[str] = None  # Форма оплаты
    sale_amount: Optional[Decimal] = None    # Сумма продаж
    return_amount: Optional[Decimal] = None  # Сумма возвратов


class PaymentGetRequest(BaseModel):
    """
    Параметры запроса для /v1/RetailReport/Payments
    start_date и end_date — обязательны (Unix time, сек).
    operating_cash_ids — необязательный массив ID касс.
    """
    start_date: int
    end_date: int
    operating_cash_ids: Optional[List[int]] = None