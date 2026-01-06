import asyncio
from dataclasses import dataclass
from typing import Dict, Optional

from aiogram import Bot, Dispatcher

from core.logger import setup_logger

logger = setup_logger("telegram_polling")


@dataclass
class _PollingSession:
    task: asyncio.Task
    bot: Bot
    dispatcher: Dispatcher


class TelegramPollingManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, _PollingSession] = {}
        self._lock = asyncio.Lock()

    async def start(self, key: str, bot: Bot, dispatcher: Dispatcher) -> None:
        await self.stop(key)
        task = asyncio.create_task(self._run_polling(key, bot, dispatcher))
        session = _PollingSession(task=task, bot=bot, dispatcher=dispatcher)
        async with self._lock:
            self._sessions[key] = session

    async def stop(self, key: str) -> None:
        session = await self._pop_session(key)
        if not session:
            return
        session.task.cancel()
        try:
            await session.task
        except asyncio.CancelledError:
            pass

    async def is_running(self, key: str) -> bool:
        async with self._lock:
            session = self._sessions.get(key)
        return bool(session and not session.task.done())

    async def _pop_session(self, key: str) -> Optional[_PollingSession]:
        async with self._lock:
            return self._sessions.pop(key, None)

    async def _run_polling(self, key: str, bot: Bot, dispatcher: Dispatcher) -> None:
        try:
            await dispatcher.start_polling(bot)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.exception("Polling error for key=%s: %s", key, error)
        finally:
            try:
                await bot.close()
            except Exception as error:
                logger.warning("Failed to close bot for key=%s: %s", key, error)
            await self._pop_session(key)


telegram_polling_manager = TelegramPollingManager()
