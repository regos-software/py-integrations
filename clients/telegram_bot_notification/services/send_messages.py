import asyncio
from typing import Dict, List


async def send_messages(
    *,
    bot,
    messages: List[Dict[str, str]],
    sleep_between: float,
    logger,
    concurrency: int = 10,
) -> Dict:
    """
    Send Telegram messages. If sleep_between is zero, messages are sent concurrently
    with a bounded semaphore; otherwise order and delay are preserved.
    """

    async def send_one(msg: Dict[str, str]) -> Dict:
        if "message" not in msg or not msg["message"]:
            return {"status": "error", "error": "Empty message text", "message": msg}

        if "recipient" not in msg or not msg["recipient"]:
            return {"status": "error", "error": "Missing recipient", "message": msg}

        chat_id = str(msg["recipient"])
        text = msg["message"]

        try:
            try:
                await bot.send_message(chat_id=chat_id, text=text)
            except Exception as error:
                error_text = str(error or "").lower()
                if not (
                    "can't parse entities" in error_text
                    or "can't find end of the entity" in error_text
                    or "unsupported start tag" in error_text
                    or "parse entities" in error_text
                ):
                    raise
                logger.warning(
                    "Telegram markdown send rejected, retrying as plain text: chat=%s error=%s",
                    chat_id,
                    error,
                )
                await bot.send_message(chat_id=chat_id, text=text, parse_mode=None)
            logger.debug("Sent Telegram message to chat %s", chat_id)
            return {"status": "sent", "chat_id": chat_id, "message": text}
        except Exception as error:
            logger.error("Telegram send error for chat %s: %s", chat_id, error)
            result = {
                "status": "error",
                "chat_id": chat_id,
                "message": text,
                "error": str(error),
            }
            migrate_to_chat_id = getattr(error, "migrate_to_chat_id", None)
            if migrate_to_chat_id:
                result["migrate_to_chat_id"] = str(migrate_to_chat_id)
            return result

    if sleep_between and sleep_between > 0:
        results: List[Dict] = []
        for msg in messages:
            results.append(await send_one(msg))
            await asyncio.sleep(sleep_between)
    else:
        semaphore = asyncio.Semaphore(max(int(concurrency or 1), 1))

        async def guarded_send(msg: Dict[str, str]) -> Dict:
            async with semaphore:
                return await send_one(msg)

        results = await asyncio.gather(*(guarded_send(msg) for msg in messages))

    sent_count = sum(1 for item in results if item["status"] == "sent")
    return {"sent_messages": sent_count, "details": results}
