# services/send_messages.py
from typing import Dict, List
import asyncio

async def send_messages(
    *,
    bot,
    messages: List[Dict[str, str]],
    sleep_between: float,
    logger,
) -> Dict:
    """
    Простая последовательная отправка сообщений.
    messages: [{ "message": "...", "recipient": "<chat_id>" }]
    """

    results: List[Dict] = []

    for msg in messages:
        if "message" not in msg or not msg["message"]:
            results.append({
                "status": "error",
                "error": "Пустой текст сообщения",
                "message": msg
            })
            continue

        if "recipient" not in msg or not msg["recipient"]:
            results.append({
                "status": "error",
                "error": "Не указан recipient (chat_id)",
                "message": msg
            })
            continue

        chat_id = str(msg["recipient"])
        text = msg["message"]

        try:
            await bot.send_message(chat_id=chat_id, text=text)
            logger.debug(f"Отправлено в чат {chat_id}: {text}")
            results.append({
                "status": "sent",
                "chat_id": chat_id,
                "message": text
            })
        except Exception as e:
            logger.error(f"Ошибка отправки в чат {chat_id}: {e}")
            results.append({
                "status": "error",
                "chat_id": chat_id,
                "message": text,
                "error": str(e)
            })

        if sleep_between and sleep_between > 0:
            await asyncio.sleep(sleep_between)

    sent_count = sum(1 for r in results if r["status"] == "sent")
    return {
        "sent_messages": sent_count,
        "details": results
    }
