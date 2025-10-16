from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel

from schemas.api.references.payment_type import PaymentType


class DocChequePayment(BaseModel):
    """
    Модель, описывающая документы розничных платежей.
    """

    uuid: str  # UUID платежа
    has_storno: bool  # Метка о том, что платеж является сторнирующим
    storno_uuid: Optional[str] = None  # UUID сторнированного платежа
    document: str  # UUID документа розничной продажи
    order: int  # Позиция в документе оплаты
    type: PaymentType  # Форма оплаты
    value: Decimal  # Сумма платежа
    has_change: bool  # Метка о том, что по платежу имеется сдача
    change_uuid: Optional[str] = None  # UUID платежа со сдачей


class DocChequePaymentGetRequest(BaseModel):
    doc_sale_uuid: Optional[str] = None
    uuids: Optional[List[str]] = None
    payment_type_ids: Optional[List[int]] = None
    stock_ids: Optional[List[int]] = None
    firm_ids: Optional[List[int]] = None
    operating_cash_ids: Optional[List[int]] = None
