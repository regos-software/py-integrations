from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from .partner_group import PartnerGroup


class LegalStatus(str, Enum):
    """
    Юридический статус контрагента.
    Значения по спецификации:
      - Legal   — юр. лицо
      - Natural — физ. лицо
    """
    Legal = "Legal"
    Natural = "Natural"


class Partner(BaseModel):
    """
    Контрагент.
    """
    id: int
    group: PartnerGroup
    legal_status: LegalStatus

    name: str
    fullname: Optional[str] = None
    boss_name: Optional[str] = None

    address: Optional[str] = None
    phones: Optional[str] = None
    description: Optional[str] = None

    inn: Optional[str] = None
    bank_name: Optional[str] = None
    mfo: Optional[str] = None
    rs: Optional[str] = None
    oked: Optional[str] = None
    vat_index: Optional[str] = None

    deleted_mark: bool
    last_update: int  # unixtime (sec)
