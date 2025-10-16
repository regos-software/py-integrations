import asyncio
import time
import threading
from typing import Dict


class TokenBucket:
    """Асинхронный токен-бакет для одного процесса/инстанса.

    rate_per_sec: токенов в секунду (скорость пополнения)
    capacity: максимальный размер ведра (бурст)
    """

    def __init__(self, rate_per_sec: float, capacity: int):
        self.rate = float(rate_per_sec)
        self.capacity = int(capacity)
        self.tokens = float(capacity)  # стартуем с полным ведром
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.updated_at
        if elapsed <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.updated_at = now

    async def acquire(self, n: float = 1.0) -> None:
        """Дождаться появления ≥ n токенов и списать их."""
        while True:
            async with self._lock:
                self._refill()
                if self.tokens >= n:
                    self.tokens -= n
                    return
                need = (n - self.tokens) / self.rate
            # Спим вне локa, чтобы не блокировать другие корутины
            await asyncio.sleep(max(need, 0.0))


# ---------- Общий реестр лимитеров по ключу (например, integration_id) ----------
_LIMITERS: Dict[str, TokenBucket] = {}
_LIMITERS_LOCK = threading.Lock()


def get_shared_limiter(key: str, rate_per_sec: float, capacity: int) -> TokenBucket:
    """Вернуть (или создать) общий лимитер для данного ключа внутри одного процесса."""
    with _LIMITERS_LOCK:
        lim = _LIMITERS.get(key)
        if lim is None:
            lim = TokenBucket(rate_per_sec, capacity)
            _LIMITERS[key] = lim
        return lim
