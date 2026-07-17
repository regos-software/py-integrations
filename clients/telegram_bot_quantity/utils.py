# utils.py
from datetime import timedelta
import json
from decimal import Decimal
from typing import Dict, List, Optional


def parse_chat_ids(raw: Optional[str]) -> List[str]:
    """
    Безопасный парсер CHAT_IDS из JSON-строки.
    Возвращает список строковых chat_id. Пустые/невалидные данные -> [].
    """
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        pass
    return []


def format_money(value) -> str:
    """
    Форматирование денег с двумя знаками после запятой и разделителями тысяч.
    Возвращает строку вида '1,234.56 '. Невалидные значения -> '0.00 '.
    """
    try:
        return f"{Decimal(value):,.2f} "
    except Exception:
        return "0.00 "


def format_timestamp(ts: Optional[int]) -> str:
    """
    Преобразует UNIX timestamp (секунды) в строку UTC.
    Невалидные значения -> 'N/A'.
    """
    from datetime import datetime, timezone

    try:
        tz = timezone(timedelta(hours=5))  # UTC+5

        return datetime.fromtimestamp(int(ts), tz=tz).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"


def extract_chat_id(update: Dict) -> Optional[str]:
    """
    Извлекает chat_id из разных типов Telegram Update.
    Возвращает str или None.
    Поддерживает:
      - message / channel_post / edited_message
      - callback_query (message.chat.id или from.id)
      - my_chat_member / chat_member
    """
    try:
        msg = update.get("message")
        if msg and isinstance(msg, dict):
            chat = msg.get("chat")
            if chat and isinstance(chat, dict) and chat.get("id") is not None:
                return str(chat["id"])

        ch_post = update.get("channel_post")
        if ch_post and isinstance(ch_post, dict):
            chat = ch_post.get("chat")
            if chat and isinstance(chat, dict) and chat.get("id") is not None:
                return str(chat["id"])

        edited = update.get("edited_message")
        if edited and isinstance(edited, dict):
            chat = edited.get("chat")
            if chat and isinstance(chat, dict) and chat.get("id") is not None:
                return str(chat["id"])

        cb = update.get("callback_query")
        if cb and isinstance(cb, dict):
            # 1) callback -> message.chat.id
            msg = cb.get("message")
            if msg and isinstance(msg, dict):
                chat = msg.get("chat")
                if chat and isinstance(chat, dict) and chat.get("id") is not None:
                    return str(chat["id"])
            # 2) приватный callback без message -> from.id
            from_user = cb.get("from")
            if (
                from_user
                and isinstance(from_user, dict)
                and from_user.get("id") is not None
            ):
                return str(from_user["id"])

        my_chat_member = update.get("my_chat_member")
        if my_chat_member and isinstance(my_chat_member, dict):
            chat = my_chat_member.get("chat")
            if chat and isinstance(chat, dict) and chat.get("id") is not None:
                return str(chat["id"])

        chat_member = update.get("chat_member")
        if chat_member and isinstance(chat_member, dict):
            chat = chat_member.get("chat")
            if chat and isinstance(chat, dict) and chat.get("id") is not None:
                return str(chat["id"])
    except Exception:
        pass

    return None
