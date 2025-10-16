from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel

from schemas.api.references.account import Account


class PaymentType(BaseModel):
    """
    Модель, описывающая форму оплаты.
    """

    id: int  # Id формы оплаты
    name: str  # Наименование формы оплаты
    account: Optional[Account] = None  # Счет, используемый для формы оплаты
    shortkey: Optional[int] = None  # Горячая клавиша
    is_cash: bool  # Метка о том, что оплата наличными
    kkm_code: int  # Код платежа в ККМ (-1 = не регистрируется)
    last_update: int  # Дата последнего изменения (unixtime, сек)
    enabled: str = None  # Доступность формы оплаты
    image_url: Optional[str] = None  # URL изображения платёжной системы
