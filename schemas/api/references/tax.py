# ==== Enums ====

from enum import Enum


class VatCalculationType(str, Enum):
    """Расчет НДС"""

    No = "No"  # Не начислять
    Exclude = "Exclude"  # В сумме
    Include = "Include"  # Сверху
