from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from .firm_group import FirmGroup


class Firm(BaseModel):
    """
    Модель, описывающая предприятия.
    """
    id: int  # ID предприятия
    group: FirmGroup  # ID группы предприятия
    name: str  # Наименование предприятия
    full_name: str  # Полное наименование предприятия
    boss_name: Optional[str] = None  # Руководитель
    address: Optional[str] = None  # Адрес
    phones: Optional[str] = None  # Телефоны
    description: Optional[str] = None  # Дополнительное описание
    inn: Optional[str] = None  # ИНН
    bank_name: Optional[str] = None  # Наименование банка
    mfo: Optional[str] = None  # МФО
    rs: Optional[str] = None  # Расчётный счёт
    oked: Optional[str] = None  # ОКЭД
    vat_index: Optional[str] = None  # Регистрационный код налогоплательщика
    deleted_mark: bool  # Метка на удаление
    last_update: int  # Дата последнего изменения (unixtime, сек)
