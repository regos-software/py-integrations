from __future__ import annotations

import asyncio
import base64
import html
import hashlib
import json
import os
import re
import socket
import time
import uuid
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

import httpx
from aiogram import Bot
from aiogram.types import BufferedInputFile, KeyboardButton, Message, ReplyKeyboardMarkup
from redis.exceptions import ResponseError
from starlette.responses import JSONResponse

from clients.base import ClientBase
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import redis_client
from schemas.api.base import APIBaseResponse
from schemas.api.chat.chat_message import (
    ChatMessageAddFileRequest,
    ChatMessageAddRequest,
    ChatMessageGetRequest,
    ChatMessageMarkReadRequest,
    ChatMessageTypeEnum,
)
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.crm.lead import (
    Lead,
    LeadAddRequest,
    LeadEditRequest,
    LeadGetRequest,
    LeadSetStatusRequest,
    LeadStatusEnum,
)
from schemas.api.crm.pipeline import CrmEntityTypeEnum, PipelineGetRequest
from schemas.api.files.file import FileGetRequest
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse
from schemas.integration.telegram_integration_base import IntegrationTelegramBase

logger = setup_logger("telegram_bot_crm_channel")


class TelegramBotCrmChannelConfig:
    INTEGRATION_KEY = "telegram_bot_crm_channel"
    REDIS_PREFIX = "clients:tg_crm_channel:"
    ALERT_EXTERNAL_PREFIX = "tgsys"

    SETTINGS_TTL = max(int(app_settings.redis_cache_ttl or 60), 30)
    DEFAULT_DEDUPE_TTL_SEC = 24 * 60 * 60
    DEFAULT_STATE_TTL_SEC = 24 * 60 * 60
    STREAM_MAXLEN = 10000
    STREAM_GROUP = "tg_crm_channel_workers"
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_READ_BLOCK_MS = 5000
    STREAM_BATCH_SIZE = 20
    STREAM_MAX_RETRIES = 5

    POLLING_LOCK_TTL_SEC = 30
    LEAD_SYNC_AVATAR_RECHECK_SEC = 6 * 60 * 60
    MAX_TELEGRAM_FILE_SIZE_BYTES = 50 * 1024 * 1024
    LARGE_FILE_NOTICE_TEXT = (
        "The file is too large to be sent. Maximum allowed size is 50 MB."
    )
    LARGE_FILES_NOTICE_TEXT = (
        "Some files are too large to be sent. Maximum allowed size is 50 MB."
    )
    RETAIL_CUSTOMER_CREATED_TEXT = (
        "\u0421\u043e\u0437\u0434\u0430\u043d \u0440\u043e\u0437\u043d\u0438\u0447\u043d\u044b\u0439 "
        "\u043f\u043e\u043a\u0443\u043f\u0430\u0442\u0435\u043b\u044c: {name}"
    )
    RETAIL_CUSTOMER_UPDATED_TEXT = (
        "\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d \u0440\u043e\u0437\u043d\u0438\u0447\u043d\u044b\u0439 "
        "\u043f\u043e\u043a\u0443\u043f\u0430\u0442\u0435\u043b\u044c: {name}"
    )
    RETAIL_CUSTOMER_ACTION_NONE = "none"
    RETAIL_CUSTOMER_ACTION_CREATED = "created"
    RETAIL_CUSTOMER_ACTION_UPDATED = "updated"
    RETAIL_CUSTOMER_ACTION_REUSED = "reused"

    SUPPORTED_INBOUND_WEBHOOKS = {
        "ChatMessageAdded",
        "ChatMessageEdited",
        "ChatMessageDeleted",
        "ChatWriting",
        "LeadClosed",
    }

    AUTO_CREATE_CONTACT_NONE = "none"
    AUTO_CREATE_CONTACT_RETAIL_CUSTOMER = "retail_customer"
    CHAT_MESSAGE_ADD_CLOSED_ENTITY_ERROR = 1220
    PHONE_PROMPT_COOLDOWN_SEC = 24 * 60 * 60
    PHONE_SHARE_BUTTON_TEXT = "Поделиться номером / Raqamni ulashish"
    PHONE_REQUEST_SENT_SYSTEM_TEXT = "Запросили у клиента номер телефона."
    PHONE_RECEIVED_SYSTEM_TEXT = "Клиент отправил номер телефона: {phone}"
    UNKNOWN_CLIENT_NAME = "Unknown"


@dataclass
class BotSlotConfig:
    slot: int
    token: str
    pipeline_id: int
    channel_id: int
    lead_subject_template: Optional[str]
    default_responsible_user_id: Optional[int]
    auto_create_contact_mode: str
    retail_customer_group_id: Optional[int]
    bot_hash: str


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    bots: List[BotSlotConfig]
    bots_by_hash: Dict[str, BotSlotConfig]
    update_mode: str
    telegram_secret_token: Optional[str]
    lead_dedupe_ttl_sec: int
    state_ttl_sec: int
    send_private_messages: bool
    forward_system_messages: bool
    lead_closed_message_template: Optional[str]
    phone_request_text: Optional[str]
    phone_share_button_text: str


_MANAGER_LOCK = asyncio.Lock()
_WORKER_TASKS: Dict[Tuple[str, str], asyncio.Task] = {}
_POLLER_TASKS: Dict[Tuple[str, str], asyncio.Task] = {}
_BOT_CLIENTS: Dict[str, Bot] = {}
_BOT_CLIENTS_LOCK = asyncio.Lock()
_HTTP_CLIENT: Optional[httpx.AsyncClient] = None
_INSTANCE_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


class TelegramFileTooLargeError(RuntimeError):
    def __init__(self, size_bytes: Optional[int], limit_bytes: int) -> None:
        self.size_bytes = size_bytes
        self.limit_bytes = limit_bytes
        super().__init__("Telegram file exceeds size limit")


class ChatMessageAddClosedEntityError(RuntimeError):
    def __init__(self, description: Optional[str] = None) -> None:
        self.description = str(description or "").strip() or None
        super().__init__(
            "ChatMessage/Add rejected for closed linked entity"
            + (f": {self.description}" if self.description else "")
        )


def _now_ts() -> int:
    return int(time.time())


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


def _redis_enabled() -> bool:
    return bool(app_settings.redis_enabled and redis_client is not None)


def _is_redis_nogroup_error(error: Exception) -> bool:
    if isinstance(error, ResponseError):
        return "NOGROUP" in str(error).upper()
    return "NOGROUP" in str(error or "").upper()


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_int(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    s = str(value).strip()
    if not s:
        return default
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def _bot_hash(token: str) -> str:
    return hashlib.md5(token.encode("utf-8")).hexdigest()


def _lead_external_id(bot_hash: str, tg_chat_id: str) -> str:
    return f"tg:{bot_hash}:{tg_chat_id}"


def _parse_tg_lead_external_id(value: Any) -> Tuple[Optional[str], Optional[str]]:
    text = str(value or "").strip()
    if not text:
        return None, None
    prefix, sep, tail = text.partition(":")
    if prefix != "tg" or not sep or not tail:
        return None, None
    bot_hash, sep2, tg_chat_id = tail.partition(":")
    bot_hash = str(bot_hash or "").strip()
    tg_chat_id = str(tg_chat_id or "").strip()
    if not sep2 or not bot_hash or not tg_chat_id:
        return None, None
    return bot_hash, tg_chat_id


def _update_mode_from_value(raw: Optional[str]) -> str:
    mode = str(raw or "").strip().lower()
    if not mode or mode == "webhook":
        return "webhook"
    if mode == "longpolling":
        return "longpolling"
    raise ValueError("telegram_update_mode must be one of: webhook, longpolling")


def _auto_create_contact_mode_from_value(raw: Optional[str]) -> str:
    mode = str(raw or "").strip().lower()
    if not mode:
        return TelegramBotCrmChannelConfig.AUTO_CREATE_CONTACT_NONE
    if mode not in {
        TelegramBotCrmChannelConfig.AUTO_CREATE_CONTACT_NONE,
        TelegramBotCrmChannelConfig.AUTO_CREATE_CONTACT_RETAIL_CUSTOMER,
    }:
        raise ValueError(
            "BOT_1_AUTO_CREATE_CONTACT must be one of: "
            f"{TelegramBotCrmChannelConfig.AUTO_CREATE_CONTACT_NONE}, "
            f"{TelegramBotCrmChannelConfig.AUTO_CREATE_CONTACT_RETAIL_CUSTOMER}"
        )
    return mode


def _tg_chat_id_cast(chat_id: str) -> Any:
    value = str(chat_id).strip()
    if value.lstrip("-").isdigit():
        try:
            return int(value)
        except ValueError:
            return value
    return value


def _sanitize_file_name(name: str) -> str:
    trimmed = (name or "").strip()
    if not trimmed:
        return "file.bin"
    return trimmed[:200]


def _normalize_phone(value: Any) -> Optional[str]:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits or None


def _normalize_telegram_name(value: Any, *, max_len: int) -> str:
    text = str(value or "")
    if not text:
        return ""
    text = text.replace("\u00A0", " ")
    text = text.replace("\u200B", "")
    text = text.replace("\u200C", "")
    text = text.replace("\u200D", "")
    text = text.replace("\uFEFF", "")
    text = re.sub(r"[\x00-\x1F\x7F]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    return text[:max_len]


def _resolve_avatar_user_id(message: Dict[str, Any]) -> Tuple[Optional[int], str]:
    contact = message.get("contact")
    contact = contact if isinstance(contact, dict) else {}
    from_author = message.get("from")
    from_author = from_author if isinstance(from_author, dict) else {}
    from_user = message.get("from_user")
    from_user = from_user if isinstance(from_user, dict) else {}
    sender_user = message.get("sender_user")
    sender_user = sender_user if isinstance(sender_user, dict) else {}
    chat = message.get("chat")
    chat = chat if isinstance(chat, dict) else {}

    candidates = [
        ("contact.user_id", contact.get("user_id")),
        ("from.id", from_author.get("id")),
        ("from_user.id", from_user.get("id")),
        ("sender_user.id", sender_user.get("id")),
    ]
    chat_type = str(chat.get("type") or "").strip().lower()
    if chat_type == "private":
        candidates.append(("chat.id", chat.get("id")))

    for source, raw in candidates:
        user_id = _parse_int(str(raw or ""), None)
        if user_id and user_id > 0:
            return int(user_id), source
    return None, "none"


def _message_has_avatar_user_hint(message: Dict[str, Any]) -> bool:
    sender_business_bot = message.get("sender_business_bot")
    if isinstance(sender_business_bot, dict):
        return False
    sender_chat = message.get("sender_chat")
    if isinstance(sender_chat, dict):
        return False

    user_id, _ = _resolve_avatar_user_id(message)
    return bool(user_id)


def _file_ext_from_name(name: str, fallback: str = "bin") -> str:
    if "." not in name:
        return fallback
    ext = name.rsplit(".", 1)[-1].strip().lower()
    if not ext:
        return fallback
    return ext[:10]


def _file_ext_from_mime(mime_type: Optional[str], fallback: str = "bin") -> str:
    mime = str(mime_type or "").strip().lower()
    if not mime:
        return fallback
    mapping = {
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/mp4": "m4a",
        "audio/x-m4a": "m4a",
        "audio/aac": "aac",
        "audio/ogg": "ogg",
        "audio/opus": "opus",
        "audio/webm": "webm",
        "audio/wav": "wav",
        "audio/x-wav": "wav",
        "audio/flac": "flac",
        "video/mp4": "mp4",
        "video/quicktime": "mov",
        "video/x-matroska": "mkv",
        "video/x-msvideo": "avi",
        "video/3gpp": "3gp",
    }
    if mime in mapping:
        return mapping[mime]
    if "/" in mime:
        tail = mime.rsplit("/", 1)[-1].strip()
        if tail:
            return tail[:10]
    return fallback


def _is_photo_extension(extension: Optional[str]) -> bool:
    return str(extension or "").lower() in {"jpg", "jpeg", "png", "webp"}


def _is_voice_extension(extension: Optional[str]) -> bool:
    return str(extension or "").lower() in {"ogg", "oga", "opus"}


def _is_audio_extension(extension: Optional[str]) -> bool:
    return str(extension or "").lower() in {
        "mp3",
        "m4a",
        "aac",
        "ogg",
        "oga",
        "opus",
        "wav",
        "flac",
        "webm",
    }


def _is_video_extension(extension: Optional[str]) -> bool:
    return str(extension or "").lower() in {
        "mp4",
        "mov",
        "m4v",
        "webm",
        "mkv",
        "avi",
        "3gp",
    }


def _headers_ci(headers: Dict[str, Any], key: str) -> Optional[str]:
    key_l = key.lower()
    for h_key, h_value in (headers or {}).items():
        if str(h_key).lower() == key_l:
            return str(h_value)
    return None


def _tg_external_message_id(bot_hash: str, tg_chat_id: str, tg_message_id: int) -> str:
    return f"tgmsg:{bot_hash}:{tg_chat_id}:{tg_message_id}"


def _is_telegram_internal_external_message(external_message_id: Optional[str]) -> bool:
    value = str(external_message_id or "").strip().lower()
    return value.startswith("tgmsg:") or value.startswith("tgsys:")


def _is_lead_entity_type(entity_type: Optional[str]) -> bool:
    value = str(entity_type or "").strip().lower()
    return value in {"lead", "2"}


def _is_user_entity_type(entity_type: Optional[str]) -> bool:
    value = str(entity_type or "").strip().lower()
    return value in {"user", "1"}


def _extract_deleted_telegram_messages(payload: Dict[str, Any]) -> List[Tuple[str, int]]:
    rows: List[Tuple[str, int]] = []

    def _push(chat_id_raw: Any, message_id_raw: Any) -> None:
        tg_chat_id = str(chat_id_raw or "").strip()
        tg_message_id = _parse_int(str(message_id_raw or ""))
        if tg_chat_id and tg_message_id:
            rows.append((tg_chat_id, tg_message_id))

    deleted_business = payload.get("deleted_business_messages")
    if isinstance(deleted_business, dict):
        chat = deleted_business.get("chat") or {}
        tg_chat_id = str(chat.get("id") or deleted_business.get("chat_id") or "").strip()
        message_ids = deleted_business.get("message_ids")
        if isinstance(message_ids, list):
            for message_id in message_ids:
                _push(tg_chat_id, message_id)

    deleted_message = payload.get("deleted_message")
    if isinstance(deleted_message, dict):
        chat = deleted_message.get("chat") or {}
        _push(
            chat.get("id") or deleted_message.get("chat_id"),
            deleted_message.get("message_id") or deleted_message.get("id"),
        )

    deleted_messages = payload.get("deleted_messages")
    if isinstance(deleted_messages, list):
        for row in deleted_messages:
            if not isinstance(row, dict):
                continue
            chat = row.get("chat") or {}
            _push(
                chat.get("id") or row.get("chat_id"),
                row.get("message_id") or row.get("id"),
            )

    deduped: List[Tuple[str, int]] = []
    seen: set[str] = set()
    for tg_chat_id, tg_message_id in rows:
        key = f"{tg_chat_id}:{tg_message_id}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append((tg_chat_id, tg_message_id))
    return deduped


_CRM_MD_TAG_MARKERS: Tuple[Tuple[str, str], ...] = (
    ("**", "b"),
    ("__", "b"),
    ("++", "u"),
    ("~~", "s"),
    ("*", "i"),
    ("_", "i"),
)
_CRM_MD_ESCAPED_CHARS = set("\\`*_+~[]()")
_LANGUAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_+\-]{0,31}$")


def _find_unescaped_token(text: str, token: str, start: int) -> int:
    if not token:
        return -1
    idx = text.find(token, max(start, 0))
    step = max(len(token), 1)
    while idx != -1:
        slash_count = 0
        probe = idx - 1
        while probe >= 0 and text[probe] == "\\":
            slash_count += 1
            probe -= 1
        if slash_count % 2 == 0:
            return idx
        idx = text.find(token, idx + step)
    return -1


def _find_markdown_link_url_end(text: str, start: int) -> int:
    depth = 1
    idx = max(start, 0)
    while idx < len(text):
        char = text[idx]
        if char == "\\" and idx + 1 < len(text):
            idx += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return idx
        idx += 1
    return -1


def _is_ascii_word_char(ch: str) -> bool:
    return bool(ch) and ch.isalnum()


def _is_valid_single_marker_bounds(text: str, open_idx: int, close_idx: int) -> bool:
    if close_idx <= open_idx + 1:
        return False
    if text[open_idx + 1].isspace() or text[close_idx - 1].isspace():
        return False
    prev_char = text[open_idx - 1] if open_idx > 0 else ""
    next_idx = close_idx + 1
    next_char = text[next_idx] if next_idx < len(text) else ""
    if prev_char and _is_ascii_word_char(prev_char):
        return False
    if next_char and _is_ascii_word_char(next_char):
        return False
    return True


def _escape_markdown_text(text: str) -> str:
    chunks: List[str] = []
    for char in text:
        if char in _CRM_MD_ESCAPED_CHARS:
            chunks.append("\\")
        chunks.append(char)
    return "".join(chunks)


def _escape_markdown_link_url(url: str) -> str:
    chunks: List[str] = []
    for char in url:
        if char in {"\\", "(", ")"}:
            chunks.append("\\")
        chunks.append(char)
    return "".join(chunks)


def _unescape_markdown_text(text: str) -> str:
    if "\\" not in text:
        return text
    chunks: List[str] = []
    idx = 0
    while idx < len(text):
        char = text[idx]
        if char == "\\" and idx + 1 < len(text):
            chunks.append(text[idx + 1])
            idx += 2
            continue
        chunks.append(char)
        idx += 1
    return "".join(chunks)


def _sanitize_code_language(raw: str) -> str:
    token = str(raw or "").strip()
    if not token:
        return ""
    if _LANGUAGE_RE.match(token):
        return token
    return ""


def _crm_markdown_to_telegram_html(markdown_text: str) -> str:
    source = str(markdown_text or "")
    if not source:
        return ""
    return _parse_crm_markdown_segment(source)


def _parse_crm_markdown_segment(text: str) -> str:
    result: List[str] = []
    idx = 0
    size = len(text)
    while idx < size:
        if text.startswith("\\", idx):
            if idx + 1 < size:
                result.append(html.escape(text[idx + 1]))
                idx += 2
                continue
            result.append("\\")
            idx += 1
            continue

        if text.startswith("```", idx):
            close_idx = _find_unescaped_token(text, "```", idx + 3)
            if close_idx != -1:
                code_block_raw = text[idx + 3 : close_idx]
                result.append(_render_markdown_code_block_to_html(code_block_raw))
                idx = close_idx + 3
                continue

        if text.startswith("`", idx):
            close_idx = _find_unescaped_token(text, "`", idx + 1)
            if close_idx != -1:
                code_inline = text[idx + 1 : close_idx]
                result.append(f"<code>{html.escape(_unescape_markdown_text(code_inline))}</code>")
                idx = close_idx + 1
                continue

        if text.startswith("[", idx):
            close_label = _find_unescaped_token(text, "]", idx + 1)
            if close_label != -1 and close_label + 1 < size and text[close_label + 1] == "(":
                close_url = _find_markdown_link_url_end(text, close_label + 2)
                if close_url != -1:
                    label_raw = text[idx + 1 : close_label]
                    url_raw = text[close_label + 2 : close_url]
                    href = _unescape_markdown_text(url_raw).strip()
                    if href:
                        label_html = _parse_crm_markdown_segment(label_raw)
                        result.append(
                            f'<a href="{html.escape(href, quote=True)}">{label_html}</a>'
                        )
                        idx = close_url + 1
                        continue

        marker_handled = False
        for marker, tag in _CRM_MD_TAG_MARKERS:
            if not text.startswith(marker, idx):
                continue
            close_idx = _find_unescaped_token(text, marker, idx + len(marker))
            if close_idx == -1:
                continue
            if len(marker) == 1 and not _is_valid_single_marker_bounds(text, idx, close_idx):
                continue
            inner_raw = text[idx + len(marker) : close_idx]
            if not inner_raw:
                continue
            inner_html = _parse_crm_markdown_segment(inner_raw)
            result.append(f"<{tag}>{inner_html}</{tag}>")
            idx = close_idx + len(marker)
            marker_handled = True
            break
        if marker_handled:
            continue

        result.append(html.escape(text[idx]))
        idx += 1

    return "".join(result)


def _render_markdown_code_block_to_html(raw_block: str) -> str:
    block = raw_block.replace("\r\n", "\n")
    language = ""
    code_text = block
    newline_idx = block.find("\n")
    if newline_idx != -1:
        candidate = block[:newline_idx].strip()
        language = _sanitize_code_language(candidate)
        if language:
            code_text = block[newline_idx + 1 :]
    code_html = html.escape(code_text)
    if language:
        return (
            '<pre><code class="language-'
            f'{html.escape(language, quote=True)}">{code_html}</code></pre>'
        )
    return f"<pre>{code_html}</pre>"


def _extract_language_from_code_tag(attrs: Dict[str, str]) -> str:
    classes = str(attrs.get("class") or "").strip().split()
    for class_name in classes:
        if class_name.startswith("language-"):
            return _sanitize_code_language(class_name[len("language-") :])
    return ""


class _TelegramHtmlToCrmMarkdownParser(HTMLParser):
    _SUPPORTED_TAGS = {
        "a",
        "b",
        "blockquote",
        "code",
        "del",
        "em",
        "i",
        "ins",
        "pre",
        "s",
        "strike",
        "strong",
        "tg-spoiler",
        "u",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: List[Dict[str, Any]] = [{"tag": None, "attrs": {}, "chunks": []}]

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag_lower = str(tag or "").lower()
        if tag_lower == "br":
            self._append_chunk("\n")
            return
        if tag_lower not in self._SUPPORTED_TAGS:
            return
        attrs_map = {str(key): str(value or "") for key, value in attrs}
        self._stack.append({"tag": tag_lower, "attrs": attrs_map, "chunks": []})

    def handle_endtag(self, tag: str) -> None:
        tag_lower = str(tag or "").lower()
        if len(self._stack) <= 1:
            return
        for idx in range(len(self._stack) - 1, 0, -1):
            frame = self._stack[idx]
            if frame.get("tag") != tag_lower:
                continue
            while len(self._stack) - 1 >= idx:
                popped = self._stack.pop()
                parent = self._stack[-1]
                rendered = self._render_frame(popped, parent)
                parent["chunks"].append(rendered)
            return

    def handle_data(self, data: str) -> None:
        if not data:
            return
        if self._inside_verbatim_context():
            self._append_chunk(data)
        else:
            self._append_chunk(_escape_markdown_text(data))

    def markdown(self) -> str:
        while len(self._stack) > 1:
            popped = self._stack.pop()
            parent = self._stack[-1]
            rendered = self._render_frame(popped, parent)
            parent["chunks"].append(rendered)
        return "".join(self._stack[0]["chunks"])

    def _append_chunk(self, text: str) -> None:
        self._stack[-1]["chunks"].append(text)

    def _inside_verbatim_context(self) -> bool:
        for frame in self._stack[1:]:
            if frame.get("tag") in {"code", "pre"}:
                return True
        return False

    def _render_frame(self, frame: Dict[str, Any], parent: Dict[str, Any]) -> str:
        tag = str(frame.get("tag") or "")
        attrs = frame.get("attrs") or {}
        content = "".join(frame.get("chunks") or [])

        if tag in {"b", "strong"}:
            return f"**{content}**"
        if tag in {"i", "em"}:
            return f"*{content}*"
        if tag in {"u", "ins"}:
            return f"++{content}++"
        if tag in {"s", "strike", "del"}:
            return f"~~{content}~~"
        if tag == "a":
            href = str(attrs.get("href") or "").strip()
            if not href:
                return content
            return f"[{content}]({_escape_markdown_link_url(href)})"
        if tag == "code":
            if str(parent.get("tag") or "") == "pre":
                language = _extract_language_from_code_tag(attrs)
                if language:
                    parent.setdefault("attrs", {})
                    parent["attrs"]["_language"] = language
                return content
            inline = content.replace("`", "\\`")
            return f"`{inline}`"
        if tag == "pre":
            language = _sanitize_code_language(str(attrs.get("_language") or ""))
            block = content.replace("```", "\\`\\`\\`")
            if block.endswith("\n"):
                if language:
                    return f"```{language}\n{block}```"
                return f"```\n{block}```"
            if language:
                return f"```{language}\n{block}\n```"
            return f"```\n{block}\n```"
        if tag in {"blockquote", "tg-spoiler"}:
            return content
        return content


def _telegram_html_to_crm_markdown(html_text: str) -> str:
    parser = _TelegramHtmlToCrmMarkdownParser()
    parser.feed(str(html_text or ""))
    parser.close()
    return parser.markdown()


def _render_links_from_telegram_entities_to_crm_markdown(
    raw_text: str, entities: List[Any]
) -> str:
    source = str(raw_text or "")
    if not source or not isinstance(entities, list):
        return source
    try:
        encoded = bytearray(source.encode("utf-16-le"))
        replacements: List[Tuple[int, int, str]] = []
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            entity_type = str(entity.get("type") or "").strip().lower()
            if entity_type not in {"url", "text_link"}:
                continue

            raw_offset = entity.get("offset")
            raw_length = entity.get("length")
            offset = _parse_int(None if raw_offset is None else str(raw_offset), None)
            length = _parse_int(None if raw_length is None else str(raw_length), None)
            if offset is None or length is None or length <= 0:
                continue

            start = int(offset) * 2
            end = (int(offset) + int(length)) * 2
            if start < 0 or end > len(encoded) or start >= end:
                continue

            label = bytes(encoded[start:end]).decode("utf-16-le", errors="ignore").strip()
            if entity_type == "url":
                url = label
            else:
                url = str(entity.get("url") or "").strip()
            if not url:
                continue

            label_text = label or url
            link_md = (
                f"[{_escape_markdown_text(label_text)}]"
                f"({_escape_markdown_link_url(url)})"
            )
            replacements.append((start, end, link_md))

        if not replacements:
            return source

        replacements.sort(key=lambda item: item[0], reverse=True)
        for start, end, replacement in replacements:
            encoded[start:end] = replacement.encode("utf-16-le")

        rendered = bytes(encoded).decode("utf-16-le", errors="ignore").strip()
        return rendered or source
    except Exception:
        return source


class TelegramBotCrmChannelIntegration(IntegrationTelegramBase, ClientBase):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _settings_cache_key(connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}settings:{connected_integration_id}"
        )

    @staticmethod
    def _stream_key(kind: str, connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}stream:{kind}:{connected_integration_id}"
        )

    @staticmethod
    def _dlq_stream_key(connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}stream:dlq:{connected_integration_id}"
        )

    @staticmethod
    def _active_ci_ids_key() -> str:
        return f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}active_ci_ids"

    @staticmethod
    # Canonical conversation cache for Telegram <-> CRM routing.
    def _mapping_by_tg_key(
        connected_integration_id: str, bot_hash: str, tg_chat_id: str
    ) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}mapping:by_tg:"
            f"{connected_integration_id}:{bot_hash}:{tg_chat_id}"
        )

    @staticmethod
    def _mapping_by_chat_key(connected_integration_id: str, chat_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}mapping:by_chat:"
            f"{connected_integration_id}:{chat_id}"
        )

    @staticmethod
    def _msgmap_regos_to_tg_key(connected_integration_id: str, chat_message_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}msgmap:regos_to_tg:"
            f"{connected_integration_id}:{chat_message_id}"
        )

    @staticmethod
    def _msgmap_tg_to_regos_key(
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
        tg_message_id: int,
    ) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}msgmap:tg_to_regos:"
            f"{connected_integration_id}:{bot_hash}:{tg_chat_id}:{tg_message_id}"
        )

    @staticmethod
    def _dedupe_tg_update_key(
        connected_integration_id: str, bot_hash: str, update_id: int
    ) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}dedupe:telegram_update:"
            f"{connected_integration_id}:{bot_hash}:{update_id}"
        )

    @staticmethod
    def _dedupe_webhook_key(connected_integration_id: str, event_hash: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}dedupe:webhook:"
            f"{connected_integration_id}:{event_hash}"
        )

    @staticmethod
    def _lock_connect_key(connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}lock:connect:"
            f"{connected_integration_id}"
        )

    @staticmethod
    def _lock_create_lead_key(
        connected_integration_id: str, bot_hash: str, tg_chat_id: str
    ) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}lock:create_lead:"
            f"{connected_integration_id}:{bot_hash}:{tg_chat_id}"
        )

    @staticmethod
    def _lock_polling_owner_key(bot_hash: str) -> str:
        return f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}lock:polling_owner:{bot_hash}"

    @staticmethod
    def _typing_key(connected_integration_id: str, bot_hash: str, tg_chat_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}typing:"
            f"{connected_integration_id}:{bot_hash}:{tg_chat_id}"
        )

    @staticmethod
    def _lead_sync_cache_key(connected_integration_id: str, lead_id: int) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}lead_sync:"
            f"{connected_integration_id}:{lead_id}"
        )

    @staticmethod
    def _retail_customer_by_tg_key(
        connected_integration_id: str, bot_hash: str, tg_chat_id: str
    ) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}retail_customer_by_tg:"
            f"{connected_integration_id}:{bot_hash}:{tg_chat_id}"
        )

    @staticmethod
    def _phone_state_key(
        connected_integration_id: str, bot_hash: str, tg_chat_id: str
    ) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}phone_state:"
            f"{connected_integration_id}:{bot_hash}:{tg_chat_id}"
        )

    @staticmethod
    def _worker_heartbeat_key(connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}worker:heartbeat:"
            f"{connected_integration_id}:{_INSTANCE_ID}"
        )

    @staticmethod
    def _parse_cached_mapping(raw: Optional[str]) -> Optional[Dict[str, Any]]:
        if not raw:
            return None
        try:
            parsed = _json_loads(raw)
        except Exception:
            return None
        if isinstance(parsed, dict):
            return parsed
        return None

    @classmethod
    async def _save_cached_mapping(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
        lead_id: int,
        chat_id: str,
    ) -> None:
        payload = _json_dumps(
            {
                "bot_hash": str(bot_hash),
                "tg_chat_id": str(tg_chat_id),
                "lead_id": int(lead_id),
                "chat_id": str(chat_id),
            }
        )
        await cls._redis_set_mapping(
            cls._mapping_by_tg_key(connected_integration_id, bot_hash, tg_chat_id),
            payload,
        )
        await cls._redis_set_mapping(
            cls._mapping_by_chat_key(connected_integration_id, str(chat_id)),
            payload,
        )

    @staticmethod
    async def _redis_set_mapping(
        key: str,
        value: str,
        ttl_sec: Optional[int] = None,
    ) -> None:
        if not _redis_enabled():
            return
        resolved_ttl = _parse_int(str(ttl_sec or ""), None)
        if not resolved_ttl or resolved_ttl <= 0:
            resolved_ttl = TelegramBotCrmChannelConfig.DEFAULT_STATE_TTL_SEC
        await redis_client.set(key, value, ex=max(resolved_ttl, 1))

    @staticmethod
    async def _redis_get(key: str) -> Optional[str]:
        if not _redis_enabled():
            return None
        return await redis_client.get(key)

    @staticmethod
    async def _redis_set_nx_with_ttl(key: str, value: str, ttl_sec: int) -> bool:
        if not _redis_enabled():
            return False
        result = await redis_client.set(key, value, ex=max(ttl_sec, 1), nx=True)
        return bool(result)

    @staticmethod
    async def _redis_set_with_ttl(key: str, value: str, ttl_sec: int) -> None:
        if not _redis_enabled():
            return
        await redis_client.set(key, value, ex=max(ttl_sec, 1))

    @staticmethod
    async def _redis_delete(*keys: str) -> None:
        if not _redis_enabled():
            return
        valid_keys = [str(k).strip() for k in keys if str(k).strip()]
        if not valid_keys:
            return
        await redis_client.delete(*valid_keys)

    @staticmethod
    async def _acquire_lock(key: str, ttl_sec: int) -> Optional[str]:
        if not _redis_enabled():
            return None
        token = uuid.uuid4().hex
        ok = await redis_client.set(key, token, ex=max(ttl_sec, 1), nx=True)
        return token if ok else None

    @staticmethod
    async def _release_lock(key: str, token: Optional[str]) -> None:
        if not (_redis_enabled() and token):
            return
        script = (
            "if redis.call('get', KEYS[1]) == ARGV[1] "
            "then return redis.call('del', KEYS[1]) else return 0 end"
        )
        try:
            await redis_client.eval(script, 1, key, token)
        except Exception:
            pass

    @staticmethod
    async def _fetch_settings_map(connected_integration_id: str) -> Dict[str, str]:
        cache_key = TelegramBotCrmChannelIntegration._settings_cache_key(
            connected_integration_id
        )
        if _redis_enabled():
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    return _json_loads(cached)
            except Exception as error:
                logger.warning("Failed to read settings cache: %s", error)

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(
                    connected_integration_id=connected_integration_id,
                )
            )
        settings_map = {
            str(row.key).strip().lower(): row.value
            for row in (response.result or [])
            if getattr(row, "key", None)
        }

        if _redis_enabled():
            try:
                await redis_client.setex(
                    cache_key,
                    TelegramBotCrmChannelConfig.SETTINGS_TTL,
                    _json_dumps(settings_map),
                )
            except Exception as error:
                logger.warning("Failed to write settings cache: %s", error)

        return settings_map

    @staticmethod
    async def _clear_settings_cache(connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        try:
            await redis_client.delete(
                TelegramBotCrmChannelIntegration._settings_cache_key(
                    connected_integration_id
                )
            )
        except Exception as error:
            logger.warning("Failed to clear settings cache: %s", error)

    @staticmethod
    def _parse_bots(settings_map: Dict[str, str]) -> List[BotSlotConfig]:
        token = str(settings_map.get("bot_1_token") or "").strip()
        pipeline_id = _parse_int(settings_map.get("bot_1_pipeline_id"))
        channel_id = _parse_int(settings_map.get("bot_1_channel_id"))
        if not token:
            raise ValueError("BOT_1_TOKEN is required")
        if not pipeline_id or pipeline_id <= 0:
            raise ValueError("BOT_1_PIPELINE_ID must be a positive integer")
        if not channel_id or channel_id <= 0:
            raise ValueError("BOT_1_CHANNEL_ID must be a positive integer")

        auto_create_contact_mode = _auto_create_contact_mode_from_value(
            settings_map.get("bot_1_auto_create_contact")
        )
        retail_customer_group_id = _parse_int(
            settings_map.get("bot_1_retail_customer_group_id")
        )
        if retail_customer_group_id is not None and retail_customer_group_id <= 0:
            raise ValueError("BOT_1_RETAIL_CUSTOMER_GROUP_ID must be a positive integer")
        if (
            auto_create_contact_mode
            == TelegramBotCrmChannelConfig.AUTO_CREATE_CONTACT_RETAIL_CUSTOMER
            and not retail_customer_group_id
        ):
            raise ValueError(
                "BOT_1_RETAIL_CUSTOMER_GROUP_ID is required when "
                "BOT_1_AUTO_CREATE_CONTACT=retail_customer"
            )

        lead_subject_template = (
            str(settings_map.get("bot_1_lead_subject_template") or "").strip()
            or "{display_name}"
        )

        return [
            BotSlotConfig(
                slot=1,
                token=token,
                pipeline_id=pipeline_id,
                channel_id=channel_id,
                lead_subject_template=lead_subject_template,
                default_responsible_user_id=_parse_int(
                    settings_map.get("bot_1_default_responsible_user_id")
                ),
                auto_create_contact_mode=auto_create_contact_mode,
                retail_customer_group_id=retail_customer_group_id,
                bot_hash=_bot_hash(token),
            )
        ]

    @staticmethod
    async def _load_runtime(connected_integration_id: str) -> RuntimeConfig:
        settings_map = await TelegramBotCrmChannelIntegration._fetch_settings_map(
            connected_integration_id
        )
        bots = TelegramBotCrmChannelIntegration._parse_bots(settings_map)
        # Transport mode is configured globally, not via integration settings.
        mode = _update_mode_from_value(app_settings.telegram_update_mode)

        runtime = RuntimeConfig(
            connected_integration_id=connected_integration_id,
            bots=bots,
            bots_by_hash={bot.bot_hash: bot for bot in bots},
            update_mode=mode,
            telegram_secret_token=str(
                settings_map.get("telegram_secret_token") or ""
            ).strip()
            or None,
            lead_dedupe_ttl_sec=max(
                _parse_int(
                    settings_map.get("lead_dedupe_ttl_sec"),
                    TelegramBotCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC,
                )
                or TelegramBotCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC,
                60,
            ),
            state_ttl_sec=max(
                _parse_int(
                    settings_map.get("state_ttl_sec"),
                    TelegramBotCrmChannelConfig.DEFAULT_STATE_TTL_SEC,
                )
                or TelegramBotCrmChannelConfig.DEFAULT_STATE_TTL_SEC,
                60,
            ),
            send_private_messages=_parse_bool(
                settings_map.get("send_private_messages"), False
            ),
            forward_system_messages=_parse_bool(
                settings_map.get("forward_system_messages"), False
            ),
            lead_closed_message_template=str(
                settings_map.get("lead_closed_message_template") or ""
            ).strip()
            or None,
            phone_request_text=str(settings_map.get("phone_request_text") or "").strip()
            or None,
            phone_share_button_text=(
                _normalize_telegram_name(
                    settings_map.get("phone_share_button_text")
                    or TelegramBotCrmChannelConfig.PHONE_SHARE_BUTTON_TEXT,
                    max_len=64,
                )
                or TelegramBotCrmChannelConfig.PHONE_SHARE_BUTTON_TEXT
            ),
        )
        return runtime

    @staticmethod
    async def _get_bot(token: str) -> Bot:
        async with _BOT_CLIENTS_LOCK:
            bot = _BOT_CLIENTS.get(token)
            if bot:
                return bot
            bot = Bot(token=token)
            _BOT_CLIENTS[token] = bot
            return bot

    @staticmethod
    async def _get_http_client() -> httpx.AsyncClient:
        global _HTTP_CLIENT
        if _HTTP_CLIENT is None:
            _HTTP_CLIENT = httpx.AsyncClient(timeout=90)
        return _HTTP_CLIENT

    @staticmethod
    async def _validate_pipelines(runtime: RuntimeConfig) -> None:
        pipeline_ids = sorted({bot.pipeline_id for bot in runtime.bots})
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.pipeline.get(
                PipelineGetRequest(
                    entity_type=CrmEntityTypeEnum.Lead,
                    ids=pipeline_ids,
                    active=True,
                    limit=max(len(pipeline_ids), 1),
                    offset=0,
                )
            )
        found_ids = {row.id for row in (response.result or []) if row and row.id}
        missing = [pid for pid in pipeline_ids if pid not in found_ids]
        if missing:
            raise ValueError(f"Pipeline not found or inactive: {missing}")

    @staticmethod
    async def _subscribe_required_webhooks(
        connected_integration_id: str,
    ) -> Dict[str, Any]:
        payload = {
            "connected_integration_id": connected_integration_id,
            "webhooks": sorted(TelegramBotCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS)
        }
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                await api.call("ConnectedIntegration/Edit", payload, APIBaseResponse)
            return {"status": "ok"}
        except Exception as error:
            logger.warning("Webhook subscription failed for %s: %s", connected_integration_id, error)
            return {"status": "failed", "error": str(error)}

    @staticmethod
    async def _enqueue(
        stream_key: str,
        fields: Dict[str, Any],
    ) -> None:
        if not _redis_enabled():
            raise RuntimeError("Redis is not enabled")
        serialized: Dict[str, str] = {}
        for key, value in fields.items():
            if isinstance(value, (dict, list)):
                serialized[key] = _json_dumps(value)
            elif value is None:
                serialized[key] = ""
            else:
                serialized[key] = str(value)
        await redis_client.xadd(
            stream_key,
            serialized,
            maxlen=TelegramBotCrmChannelConfig.STREAM_MAXLEN,
            approximate=True,
        )

    @staticmethod
    async def _ensure_consumer_group(stream_key: str) -> None:
        if not _redis_enabled():
            return
        try:
            await redis_client.xgroup_create(
                stream_key,
                TelegramBotCrmChannelConfig.STREAM_GROUP,
                id="0-0",
                mkstream=True,
            )
        except Exception as error:
            if "BUSYGROUP" not in str(error):
                raise

    @classmethod
    async def _ensure_stream_workers(cls, connected_integration_id: str) -> None:
        async with _MANAGER_LOCK:
            for kind in ("telegram_in", "regos_in"):
                key = (connected_integration_id, kind)
                task = _WORKER_TASKS.get(key)
                if task and not task.done():
                    continue
                _WORKER_TASKS[key] = asyncio.create_task(
                    cls._stream_worker_loop(connected_integration_id, kind),
                    name=f"tg_crm_stream_{kind}_{connected_integration_id}",
                )

    @classmethod
    async def _stop_stream_workers(cls, connected_integration_id: str) -> None:
        async with _MANAGER_LOCK:
            keys = [k for k in _WORKER_TASKS if k[0] == connected_integration_id]
            tasks = [_WORKER_TASKS.pop(k) for k in keys]
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error while stopping stream worker")

    @classmethod
    async def _ensure_poller(
        cls, connected_integration_id: str, bot_config: BotSlotConfig
    ) -> None:
        key = (connected_integration_id, bot_config.bot_hash)
        async with _MANAGER_LOCK:
            task = _POLLER_TASKS.get(key)
            if task and not task.done():
                return
            _POLLER_TASKS[key] = asyncio.create_task(
                cls._polling_loop(connected_integration_id, bot_config),
                name=f"tg_crm_poll_{connected_integration_id}_{bot_config.bot_hash}",
            )

    @classmethod
    async def _stop_pollers_for_ci(
        cls, connected_integration_id: str, keep_hashes: Optional[set[str]] = None
    ) -> None:
        keep_hashes = keep_hashes or set()
        async with _MANAGER_LOCK:
            keys = [
                key
                for key in _POLLER_TASKS
                if key[0] == connected_integration_id and key[1] not in keep_hashes
            ]
            tasks = [_POLLER_TASKS.pop(key) for key in keys]
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error while stopping poller")

    async def connect(self, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        lock_key = self._lock_connect_key(self.connected_integration_id)
        lock_token = await self._acquire_lock(lock_key, 30)
        if not lock_token:
            return self._error_response(1002, "connect is already running").dict()

        runtime: Optional[RuntimeConfig] = None
        try:
            runtime = await self._load_runtime(self.connected_integration_id)
            logger.info(
                "telegram_update_mode=%s ci=%s",
                runtime.update_mode,
                self.connected_integration_id,
            )
            logger.debug(
                "connect runtime: ci=%s bots=%s bot_hashes=%s",
                self.connected_integration_id,
                len(runtime.bots),
                [b.bot_hash for b in runtime.bots],
            )
            await self._validate_pipelines(runtime)
            webhook_subscribe = await self._subscribe_required_webhooks(
                self.connected_integration_id
            )

            if runtime.update_mode == "longpolling":
                keep_hashes = {bot.bot_hash for bot in runtime.bots}
                await self._stop_pollers_for_ci(
                    self.connected_integration_id, keep_hashes=keep_hashes
                )
                for bot_cfg in runtime.bots:
                    bot = await self._get_bot(bot_cfg.token)
                    await bot.delete_webhook(drop_pending_updates=True)
                    await self._ensure_poller(self.connected_integration_id, bot_cfg)
                await self._ensure_stream_workers(self.connected_integration_id)
                await redis_client.sadd(
                    self._active_ci_ids_key(), self.connected_integration_id
                )
                return {
                    "status": "connected",
                    "mode": "longpolling",
                    "bots": len(runtime.bots),
                    "webhooks_subscription": webhook_subscribe,
                }

            await self._stop_pollers_for_ci(self.connected_integration_id)
            bot_cfg = runtime.bots[0]
            bot = await self._get_bot(bot_cfg.token)
            url = (
                f"{app_settings.integration_url.rstrip('/')}/external/"
                f"{self.connected_integration_id}/external/"
            )
            await bot.delete_webhook(drop_pending_updates=True)
            kwargs_set_webhook: Dict[str, Any] = {"url": url}
            if runtime.telegram_secret_token:
                kwargs_set_webhook["secret_token"] = runtime.telegram_secret_token
            await bot.set_webhook(**kwargs_set_webhook)
            await self._ensure_stream_workers(self.connected_integration_id)
            await redis_client.sadd(self._active_ci_ids_key(), self.connected_integration_id)

            return {
                "status": "connected",
                "mode": "webhook",
                "bots": len(runtime.bots),
                "webhook_url": url,
                "bot_hash": bot_cfg.bot_hash,
                "webhooks_subscription": webhook_subscribe,
            }
        except Exception as error:
            try:
                await self._stop_pollers_for_ci(self.connected_integration_id)
                await self._stop_stream_workers(self.connected_integration_id)
                await redis_client.srem(
                    self._active_ci_ids_key(), self.connected_integration_id
                )
            except Exception as rollback_error:
                logger.warning(
                    "connect rollback failed: ci=%s error=%s",
                    self.connected_integration_id,
                    rollback_error,
                )

            logger.exception("connect failed: %s", error)
            error_text = str(error)
            if (
                runtime
                and runtime.update_mode == "webhook"
                and "bad webhook" in error_text.lower()
                and "failed to resolve host" in error_text.lower()
            ):
                error_text = (
                    "webhook setup failed: Telegram cannot resolve webhook host. "
                    "Use a public HTTPS domain in integration_url or set "
                    "app_settings.telegram_update_mode=longpolling."
                )
            return self._error_response(1003, f"connect failed: {error_text}").dict()
        finally:
            await self._release_lock(lock_key, lock_token)

    async def disconnect(self, **kwargs) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        try:
            runtime: Optional[RuntimeConfig] = None
            try:
                runtime = await self._load_runtime(self.connected_integration_id)
            except Exception:
                runtime = None

            await self._stop_pollers_for_ci(self.connected_integration_id)
            if runtime:
                for bot_cfg in runtime.bots:
                    try:
                        bot = await self._get_bot(bot_cfg.token)
                        await bot.delete_webhook(drop_pending_updates=True)
                    except Exception as error:
                        logger.warning(
                            "Failed to delete webhook for bot_hash=%s: %s",
                            bot_cfg.bot_hash,
                            error,
                        )

            await self._stop_stream_workers(self.connected_integration_id)
            await redis_client.srem(self._active_ci_ids_key(), self.connected_integration_id)
            return {"status": "disconnected"}
        except Exception as error:
            logger.exception("disconnect failed: %s", error)
            return self._error_response(1004, f"disconnect failed: {error}").dict()

    async def reconnect(self, **kwargs) -> Dict[str, Any]:
        await self.disconnect()
        return await self.connect()

    async def update_settings(self, **kwargs) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self._clear_settings_cache(self.connected_integration_id)
        result = await self.reconnect()
        return {"status": "settings updated", "reconnect": result}

    async def send_messages(self, messages: List[Dict]) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        try:
            runtime = await self._load_runtime(self.connected_integration_id)
            bot_cfg = runtime.bots[0]
            details: List[Dict[str, Any]] = []
            for item in messages:
                text = str(item.get("message") or "").strip()
                recipient = str(item.get("recipient") or "").strip()
                bot_hash = str(item.get("bot_hash") or "").strip()
                if not text or not recipient:
                    details.append({"status": "error", "error": "recipient/message required"})
                    continue
                if bot_hash and bot_hash != bot_cfg.bot_hash:
                    details.append(
                        {
                            "status": "error",
                            "error": "single-bot mode: unknown bot_hash",
                        }
                    )
                    continue
                bot = await self._get_bot(bot_cfg.token)
                sent = await bot.send_message(chat_id=_tg_chat_id_cast(recipient), text=text)
                details.append(
                    {
                        "status": "sent",
                        "bot_hash": bot_cfg.bot_hash,
                        "recipient": recipient,
                        "telegram_message_id": sent.message_id,
                    }
                )
            return {"sent": len([row for row in details if row["status"] == "sent"]), "details": details}
        except Exception as error:
            logger.exception("send_messages failed: %s", error)
            return self._error_response(1005, f"send_messages failed: {error}").dict()

    async def handle_external(self, envelope: Dict) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return JSONResponse(
                status_code=503,
                content=self._error_response(1001, "Redis is required for this integration").dict(),
            )

        payload = envelope.get("body")
        if not isinstance(payload, dict):
            return self._error_response(400, "Invalid Telegram payload").dict()

        runtime = await self._load_runtime(self.connected_integration_id)
        single_bot = runtime.bots[0]
        query = envelope.get("query") or {}
        query_bot_hash = str(query.get("bot_hash") or "").strip()
        if query_bot_hash and query_bot_hash != single_bot.bot_hash:
            return self._error_response(
                400, "single-bot mode: invalid bot_hash for Telegram webhook"
            ).dict()
        bot_hash = single_bot.bot_hash

        if runtime.telegram_secret_token:
            headers = envelope.get("headers") or {}
            actual_secret = _headers_ci(headers, "x-telegram-bot-api-secret-token")
            if actual_secret != runtime.telegram_secret_token:
                return self._error_response(403, "Invalid Telegram secret token").dict()

        try:
            logger.debug(
                "enqueue telegram webhook: ci=%s bot_hash=%s update_id=%s",
                self.connected_integration_id,
                bot_hash,
                payload.get("update_id"),
            )
            await self._enqueue(
                self._stream_key("telegram_in", self.connected_integration_id),
                {
                    "connected_integration_id": self.connected_integration_id,
                    "bot_hash": bot_hash,
                    "payload": payload,
                    "attempt": "0",
                    "enqueued_at": str(_now_ts()),
                },
            )
        except Exception as error:
            logger.exception("Failed to enqueue Telegram event: %s", error)
            return JSONResponse(
                status_code=503,
                content=self._error_response(503, f"enqueue failed: {error}").dict(),
            )

        await self._ensure_stream_workers(self.connected_integration_id)
        return {"status": "accepted"}

    async def handle_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        event_action, event_data, event_id = self._normalize_regos_webhook_payload(
            action=action,
            data=data,
            kwargs=kwargs,
        )
        if not event_action:
            return self._error_response(400, "Webhook action is not provided").dict()
        if event_action not in TelegramBotCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS:
            return {"status": "ignored", "action": event_action}

        try:
            logger.debug(
                "enqueue regos webhook: ci=%s action=%s event_id=%s",
                self.connected_integration_id,
                event_action,
                event_id,
            )
            await self._enqueue(
                self._stream_key("regos_in", self.connected_integration_id),
                {
                    "connected_integration_id": self.connected_integration_id,
                    "action": event_action,
                    "payload": event_data or {},
                    "event_id": event_id or "",
                    "attempt": "0",
                    "enqueued_at": str(_now_ts()),
                },
            )
        except Exception as error:
            logger.exception("Failed to enqueue REGOS webhook: %s", error)
            return self._error_response(503, f"enqueue failed: {error}").dict()

        await self._ensure_stream_workers(self.connected_integration_id)
        return {"status": "accepted", "action": event_action}

    @staticmethod
    def _normalize_regos_webhook_payload(
        action: Optional[str], data: Optional[Dict], kwargs: Dict[str, Any]
    ) -> Tuple[Optional[str], Dict[str, Any], Optional[str]]:
        event_id = str(kwargs.get("event_id") or "").strip() or None

        # Canonical webhook call: action + payload in method params.
        if isinstance(action, str) and action in TelegramBotCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS:
            return action, data or {}, event_id

        # Wrapped call used by some gateways: action=HandleWebhook with nested action/data.
        if action == "HandleWebhook":
            payload = data if isinstance(data, dict) else {}
            nested = payload.get("data")
            wrapped_event_id = (
                str(payload.get("event_id") or event_id or "").strip() or None
            )
            if not isinstance(nested, dict):
                return None, {}, wrapped_event_id
            nested_action = nested.get("action")
            nested_data = nested.get("data")
            if not isinstance(nested_action, str) or not isinstance(nested_data, dict):
                return None, {}, wrapped_event_id
            return nested_action, nested_data, wrapped_event_id

        # Alternative canonical envelope: data={"action": "...", "data": {...}, "event_id": "..."}.
        if isinstance(data, dict):
            nested_action = data.get("action")
            nested_data = data.get("data")
            nested_event_id = str(data.get("event_id") or event_id or "").strip() or None
            if isinstance(nested_action, str) and isinstance(nested_data, dict):
                return nested_action, nested_data, nested_event_id

        return None, {}, event_id

    @staticmethod
    def _error_response(code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    def _extract_message_author(message: Dict[str, Any]) -> Dict[str, Any]:
        author = message.get("from")
        if isinstance(author, dict):
            return author
        author = message.get("from_user")
        if isinstance(author, dict):
            return author
        return {}

    @classmethod
    def _extract_own_contact_phone(cls, message: Dict[str, Any]) -> Optional[str]:
        contact = message.get("contact")
        if not isinstance(contact, dict):
            return None

        raw_phone = str(contact.get("phone_number") or "").strip()
        if not raw_phone:
            return None
        normalized_phone = _normalize_phone(raw_phone)
        if not normalized_phone:
            return None

        author = cls._extract_message_author(message)
        author_id = _parse_int(str(author.get("id") or ""), None)
        contact_user_id = _parse_int(str(contact.get("user_id") or ""), None)
        if not author_id or not contact_user_id or author_id != contact_user_id:
            logger.debug(
                "Skip contact phone due owner mismatch: author_id=%s contact_user_id=%s",
                author_id,
                contact_user_id,
            )
            return None
        return normalized_phone

    @staticmethod
    def _is_private_chat_message(message: Dict[str, Any]) -> bool:
        chat = message.get("chat")
        if not isinstance(chat, dict):
            return False
        return str(chat.get("type") or "").strip().lower() == "private"

    @staticmethod
    def _parse_phone_state(raw: Optional[str]) -> Optional[Dict[str, Any]]:
        payload = TelegramBotCrmChannelIntegration._parse_cached_mapping(raw)
        if not payload:
            return None

        lead_raw = payload.get("lead_has_phone")
        retail_raw = payload.get("retail_has_phone")
        prompted_raw = payload.get("prompted_at_ts")
        return {
            "lead_has_phone": lead_raw if isinstance(lead_raw, bool) else _parse_bool(str(lead_raw), False),
            "retail_has_phone": retail_raw
            if isinstance(retail_raw, bool)
            else _parse_bool(str(retail_raw), False),
            "prompted_at_ts": max(_parse_int(str(prompted_raw or ""), 0) or 0, 0),
        }

    @staticmethod
    def _build_phone_state_payload(
        lead_has_phone: bool,
        retail_has_phone: bool,
        prompted_at_ts: int,
    ) -> Dict[str, Any]:
        return {
            "lead_has_phone": bool(lead_has_phone),
            "retail_has_phone": bool(retail_has_phone),
            "prompted_at_ts": max(int(prompted_at_ts or 0), 0),
        }

    @classmethod
    async def _save_phone_state(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
        *,
        lead_has_phone: bool,
        retail_has_phone: bool,
        prompted_at_ts: int,
        ttl_sec: int,
    ) -> None:
        await cls._redis_set_mapping(
            cls._phone_state_key(connected_integration_id, bot_hash, tg_chat_id),
            _json_dumps(
                cls._build_phone_state_payload(
                    lead_has_phone=lead_has_phone,
                    retail_has_phone=retail_has_phone,
                    prompted_at_ts=prompted_at_ts,
                )
            ),
            ttl_sec,
        )

    @classmethod
    async def _resolve_lead_has_phone_best_effort(
        cls,
        connected_integration_id: str,
        lead_id: int,
    ) -> Optional[bool]:
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                lead = await api.crm.lead.get_by_id(lead_id)
            if not lead:
                return None
            return bool(_normalize_phone(getattr(lead, "client_phone", None)))
        except Exception as error:
            logger.warning(
                "Lead/Get failed while checking phone presence: ci=%s lead_id=%s error=%s",
                connected_integration_id,
                lead_id,
                error,
            )
            return None

    @classmethod
    async def _resolve_retail_has_phone_best_effort(
        cls,
        connected_integration_id: str,
        tg_chat_id: str,
        customer_id: Optional[int],
    ) -> Optional[bool]:
        try:
            if customer_id and customer_id > 0:
                async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                    resp = await api.call(
                        "RetailCustomer/Get",
                        {"ids": [customer_id], "limit": 1, "offset": 0},
                        APIBaseResponse[List[Dict[str, Any]]],
                    )
                if not resp.ok:
                    logger.warning(
                        "RetailCustomer/Get rejected while checking phone presence: ci=%s customer_id=%s payload=%s",
                        connected_integration_id,
                        customer_id,
                        resp.result,
                    )
                    return None
                if resp.ok and isinstance(resp.result, list) and resp.result:
                    row = resp.result[0]
                    if isinstance(row, dict):
                        return bool(_normalize_phone(row.get("main_phone")))

            existing_row = await cls._find_existing_retail_customer(
                connected_integration_id=connected_integration_id,
                tg_chat_id=tg_chat_id,
            )
            if isinstance(existing_row, dict):
                return bool(_normalize_phone(existing_row.get("main_phone")))
            return False
        except Exception as error:
            logger.warning(
                "RetailCustomer/Get failed while checking phone presence: ci=%s tg_chat_id=%s customer_id=%s error=%s",
                connected_integration_id,
                tg_chat_id,
                customer_id,
                error,
            )
            return None

    @classmethod
    async def _maybe_request_phone_best_effort(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        bot_cfg: BotSlotConfig,
        lead_id: int,
        chat_id: str,
        tg_chat_id: str,
        message: Dict[str, Any],
        customer_id: Optional[int],
        retail_has_phone_hint: Optional[bool],
    ) -> None:
        request_text = cls._normalize_text_value(runtime.phone_request_text)
        if not request_text or not cls._is_private_chat_message(message):
            return

        own_contact_phone = cls._extract_own_contact_phone(message)
        own_contact_has_phone = bool(_normalize_phone(own_contact_phone))
        retail_required = (
            bot_cfg.auto_create_contact_mode
            == TelegramBotCrmChannelConfig.AUTO_CREATE_CONTACT_RETAIL_CUSTOMER
            and bool(bot_cfg.retail_customer_group_id)
        )

        state = cls._parse_phone_state(
            await cls._redis_get(
                cls._phone_state_key(connected_integration_id, bot_cfg.bot_hash, tg_chat_id)
            )
        )
        prompted_at_ts = int(state.get("prompted_at_ts") or 0) if state else 0

        if own_contact_has_phone:
            message_id = _parse_int(str(message.get("message_id") or ""), None) or _now_ts()
            phone_text = (
                cls._normalize_text_value(own_contact_phone) or "не указан"
            )
            await cls._send_phone_system_message_best_effort(
                connected_integration_id=connected_integration_id,
                chat_id=chat_id,
                external_message_id=(
                    f"tgsys:phone_received:{bot_cfg.bot_hash}:{tg_chat_id}:{message_id}"
                ),
                text=TelegramBotCrmChannelConfig.PHONE_RECEIVED_SYSTEM_TEXT.format(
                    phone=phone_text
                ),
            )
            await cls._save_phone_state(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_cfg.bot_hash,
                tg_chat_id=tg_chat_id,
                lead_has_phone=True,
                retail_has_phone=True,
                prompted_at_ts=0,
                ttl_sec=runtime.state_ttl_sec,
            )
            return

        lead_has_phone: Optional[bool] = None
        retail_has_phone: Optional[bool] = None
        if state:
            lead_has_phone = bool(state.get("lead_has_phone"))
            retail_has_phone = bool(state.get("retail_has_phone"))

        if lead_has_phone is None or not state:
            lead_has_phone = await cls._resolve_lead_has_phone_best_effort(
                connected_integration_id=connected_integration_id,
                lead_id=lead_id,
            )

        if retail_required:
            if retail_has_phone_hint is not None:
                retail_has_phone = bool(retail_has_phone_hint)
            elif retail_has_phone is None or not state:
                retail_has_phone = await cls._resolve_retail_has_phone_best_effort(
                    connected_integration_id=connected_integration_id,
                    tg_chat_id=tg_chat_id,
                    customer_id=customer_id,
                )
        else:
            retail_has_phone = True

        if lead_has_phone is None or retail_has_phone is None:
            return

        cooldown_sec = max(TelegramBotCrmChannelConfig.PHONE_PROMPT_COOLDOWN_SEC, 60)
        now_ts = _now_ts()
        need_prompt = not lead_has_phone or not retail_has_phone

        # Before sending a repeated prompt, re-check CRM once to avoid stale cache.
        if need_prompt and prompted_at_ts and now_ts - prompted_at_ts >= cooldown_sec:
            refreshed_lead = await cls._resolve_lead_has_phone_best_effort(
                connected_integration_id=connected_integration_id,
                lead_id=lead_id,
            )
            if refreshed_lead is not None:
                lead_has_phone = refreshed_lead
            if retail_required and retail_has_phone_hint is None:
                refreshed_retail = await cls._resolve_retail_has_phone_best_effort(
                    connected_integration_id=connected_integration_id,
                    tg_chat_id=tg_chat_id,
                    customer_id=customer_id,
                )
                if refreshed_retail is not None:
                    retail_has_phone = refreshed_retail
            need_prompt = not lead_has_phone or not retail_has_phone

        if need_prompt and (not prompted_at_ts or now_ts - prompted_at_ts >= cooldown_sec):
            try:
                bot = await cls._get_bot(bot_cfg.token)
                await bot.send_message(
                    chat_id=_tg_chat_id_cast(tg_chat_id),
                    text=request_text,
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[
                            [
                                KeyboardButton(
                                    text=runtime.phone_share_button_text,
                                    request_contact=True,
                                )
                            ]
                        ],
                        resize_keyboard=True,
                        one_time_keyboard=True,
                    ),
                )
                prompted_at_ts = now_ts
                message_id = _parse_int(str(message.get("message_id") or ""), None) or now_ts
                await cls._send_phone_system_message_best_effort(
                    connected_integration_id=connected_integration_id,
                    chat_id=chat_id,
                    external_message_id=(
                        f"tgsys:phone_request_prompt:{bot_cfg.bot_hash}:{tg_chat_id}:{message_id}"
                    ),
                    text=TelegramBotCrmChannelConfig.PHONE_REQUEST_SENT_SYSTEM_TEXT,
                )
            except Exception as error:
                logger.warning(
                    "Failed to send phone request prompt: ci=%s bot_hash=%s tg_chat_id=%s error=%s",
                    connected_integration_id,
                    bot_cfg.bot_hash,
                    tg_chat_id,
                    error,
                )

        await cls._save_phone_state(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_cfg.bot_hash,
            tg_chat_id=tg_chat_id,
            lead_has_phone=bool(lead_has_phone),
            retail_has_phone=bool(retail_has_phone),
            prompted_at_ts=prompted_at_ts if need_prompt else 0,
            ttl_sec=runtime.state_ttl_sec,
        )

    @classmethod
    def _telegram_message_to_crm_markdown(
        cls, connected_integration_id: str, message: Dict[str, Any]
    ) -> Optional[str]:
        body_text = cls._telegram_message_body_to_crm_markdown(
            connected_integration_id=connected_integration_id,
            message=message,
        )

        reply_message = message.get("reply_to_message")
        if not isinstance(reply_message, dict):
            return body_text

        reply_text = cls._telegram_message_body_to_crm_markdown(
            connected_integration_id=connected_integration_id,
            message=reply_message,
        )
        if not reply_text:
            reply_text = cls._reply_message_placeholder_text(reply_message)

        reply_quote = cls._build_crm_reply_quote(reply_text)
        if not reply_quote:
            return body_text
        if body_text:
            return f"{reply_quote}\n\n{body_text}"
        return reply_quote

    @classmethod
    def _telegram_message_body_to_crm_markdown(
        cls, connected_integration_id: str, message: Dict[str, Any]
    ) -> Optional[str]:
        has_text = message.get("text") is not None
        raw_text = (
            str(message.get("text") or "").strip()
            if has_text
            else str(message.get("caption") or "").strip()
        )
        if not raw_text:
            return None

        entities_key = "entities" if has_text else "caption_entities"
        entities = message.get(entities_key)
        if not isinstance(entities, list) or not entities:
            return raw_text
        links_fallback_text = _render_links_from_telegram_entities_to_crm_markdown(
            raw_text, entities
        )

        try:
            tg_message = Message.model_validate(message)
            html_text = str(tg_message.html_text or "").strip()
            if not html_text:
                return links_fallback_text or raw_text
            markdown_text = _telegram_html_to_crm_markdown(html_text).strip()
            if markdown_text:
                logger.debug(
                    "Telegram formatting converted to CRM markdown: ci=%s entities=%s source=%s",
                    connected_integration_id,
                    len(entities),
                    entities_key,
                )
                return markdown_text
        except Exception as error:
            logger.debug(
                "Telegram formatting conversion failed (fallback to plain text): ci=%s source=%s error=%s",
                connected_integration_id,
                entities_key,
                error,
            )
        return links_fallback_text or raw_text

    @staticmethod
    def _reply_message_placeholder_text(message: Dict[str, Any]) -> str:
        if message.get("photo"):
            return "[Фото]"
        if message.get("video"):
            return "[Видео]"
        if message.get("voice"):
            return "[Голосовое сообщение]"
        if message.get("audio"):
            return "[Аудио]"
        if message.get("document"):
            return "[Файл]"
        if message.get("sticker"):
            return "[Стикер]"
        if message.get("contact"):
            return "[Контакт]"
        if message.get("location"):
            return "[Локация]"
        if message.get("poll"):
            return "[Опрос]"
        return "[Сообщение]"

    @staticmethod
    def _build_crm_reply_quote(text: Optional[str]) -> Optional[str]:
        raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not raw:
            return None

        max_chars = 700
        max_lines = 6
        truncated = False

        if len(raw) > max_chars:
            raw = raw[:max_chars].rstrip()
            truncated = True

        lines = raw.split("\n")
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            truncated = True

        quote_lines: List[str] = []
        for line in lines:
            escaped = _escape_markdown_text(line.strip())
            quote_lines.append(f"> {escaped}" if escaped else ">")
        if truncated:
            quote_lines.append("> ...")

        result = "\n".join(quote_lines).strip()
        return result or None

    @staticmethod
    def _crm_markdown_to_telegram_payload(text: str) -> Tuple[str, Optional[str]]:
        source = str(text or "")
        if not source:
            return "", None
        try:
            return _crm_markdown_to_telegram_html(source), "HTML"
        except Exception:
            return source, None

    @staticmethod
    def _extract_contact_payload(message: Dict[str, Any], tg_chat_id: str) -> Dict[str, str]:
        author = TelegramBotCrmChannelIntegration._extract_message_author(message)
        contact = message.get("contact")
        contact = contact if isinstance(contact, dict) else {}
        chat = message.get("chat") or {}

        first_name_raw = (
            str(contact.get("first_name") or "").strip()
            or str(author.get("first_name") or "").strip()
            or str(chat.get("first_name") or "").strip()
        )
        last_name_raw = (
            str(contact.get("last_name") or "").strip()
            or str(author.get("last_name") or "").strip()
            or str(chat.get("last_name") or "").strip()
        )
        username_raw = (
            str(author.get("username") or "").strip()
            or str(chat.get("username") or "").strip()
        )
        first_name = _normalize_telegram_name(first_name_raw, max_len=120)
        last_name = _normalize_telegram_name(last_name_raw, max_len=120)
        username = _normalize_telegram_name(username_raw, max_len=64).lstrip("@")
        username = re.sub(r"\s+", "", username)

        if not first_name:
            first_name = _normalize_telegram_name(username, max_len=120)
        if not first_name:
            first_name = TelegramBotCrmChannelConfig.UNKNOWN_CLIENT_NAME

        full_name = _normalize_telegram_name(
            " ".join([part for part in [first_name, last_name] if part]),
            max_len=250,
        )
        display_name = _normalize_telegram_name(
            full_name or username or TelegramBotCrmChannelConfig.UNKNOWN_CLIENT_NAME,
            max_len=250,
        ) or TelegramBotCrmChannelConfig.UNKNOWN_CLIENT_NAME

        return {
            "chat_id": tg_chat_id,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "full_name": full_name,
            "display_name": display_name,
        }

    @staticmethod
    def _build_subject(template: Optional[str], message: Dict[str, Any], tg_chat_id: str) -> str:
        payload = TelegramBotCrmChannelIntegration._extract_contact_payload(
            message, tg_chat_id
        )
        if template:
            try:
                result = _normalize_telegram_name(template.format_map(payload), max_len=250)
                if result:
                    return result
            except Exception as error:
                logger.warning(
                    "Invalid bot_1_lead_subject_template; fallback to display_name: %s",
                    error,
                )
        return _normalize_telegram_name(payload["display_name"] or tg_chat_id, max_len=250)

    @classmethod
    def _build_retail_customer_payload(
        cls, message: Dict[str, Any], tg_chat_id: str
    ) -> Dict[str, Optional[str]]:
        contact_payload = cls._extract_contact_payload(message, tg_chat_id)
        first_name = (
            cls._normalize_text_value(contact_payload.get("first_name"))
            or cls._normalize_text_value(contact_payload.get("display_name"))
            or tg_chat_id
        )
        last_name = cls._normalize_text_value(contact_payload.get("last_name"))
        full_name = cls._normalize_text_value(contact_payload.get("full_name"))
        if not full_name:
            full_name = " ".join([part for part in [first_name, last_name] if part]).strip() or None

        phone = _normalize_phone(cls._extract_own_contact_phone(message))

        return {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "main_phone": phone,
        }

    @classmethod
    async def _find_existing_retail_customer(
        cls,
        connected_integration_id: str,
        tg_chat_id: str,
    ) -> Optional[Dict[str, Any]]:
        telegram_id = cls._normalize_text_value(tg_chat_id)
        if not telegram_id:
            return None
        payload = {
            "filters": [
                Filter(
                    field="field_telegram_id",
                    operator=FilterOperator.Equal,
                    value=telegram_id,
                ).model_dump(mode="json")
            ],
            "limit": 10,
            "offset": 0,
        }
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            resp = await api.call(
                "RetailCustomer/Get",
                payload,
                APIBaseResponse[List[Dict[str, Any]]],
            )
        if not resp.ok:
            response_payload = resp.result if isinstance(resp.result, dict) else {}
            error_code = response_payload.get("error")
            description = str(response_payload.get("description") or "").lower()
            if error_code == 7501 or "field_telegram_id" in description:
                logger.warning(
                    "RetailCustomer/Get by field_telegram_id is not available: %s",
                    resp.result,
                )
                return None
            logger.warning(
                "RetailCustomer/Get rejected during pre-create telegram lookup: payload=%s result=%s",
                payload,
                resp.result,
            )
            return None
        rows = resp.result if isinstance(resp.result, list) else []
        if resp.result is not None and not isinstance(resp.result, list):
            logger.warning("RetailCustomer/Get returned non-list result")
            return None

        matched_rows: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            found_id = _parse_int(str(row.get("id") or ""))
            if not found_id or found_id <= 0:
                continue
            fields = row.get("fields")
            if not isinstance(fields, list):
                continue
            for field_row in fields:
                if not isinstance(field_row, dict):
                    continue
                if str(field_row.get("key") or "") != "field_telegram_id":
                    continue
                if str(field_row.get("value") or "") == telegram_id:
                    matched_rows.append(row)
                    break
        if len(matched_rows) == 1:
            return matched_rows[0]
        if len(matched_rows) > 1:
            matched_ids = [
                _parse_int(str(row.get("id") or ""))
                for row in matched_rows
                if isinstance(row, dict)
            ]
            logger.warning(
                "RetailCustomer pre-create lookup is ambiguous by field_telegram_id: "
                "ci=%s tg_chat_id=%s matched_ids=%s",
                connected_integration_id,
                telegram_id,
                matched_ids,
            )
            return None

        if rows and isinstance(rows[0], dict):
            # Fallback for installations where `fields` are not returned in payload.
            fallback_id = _parse_int(str(rows[0].get("id") or ""))
            if fallback_id and fallback_id > 0:
                return rows[0]
        return None

    @classmethod
    def _retail_customer_name(cls, customer_payload: Dict[str, Optional[str]], tg_chat_id: str) -> str:
        return (
            cls._normalize_text_value(customer_payload.get("full_name"))
            or cls._normalize_text_value(customer_payload.get("first_name"))
            or tg_chat_id
        )

    @staticmethod
    def _extract_field_value(fields: Any, key: str) -> Optional[str]:
        if not isinstance(fields, list):
            return None
        for row in fields:
            if not isinstance(row, dict):
                continue
            if str(row.get("key") or "") != key:
                continue
            return str(row.get("value") or "")
        return None

    @classmethod
    def _build_retail_customer_edit_payload(
        cls,
        customer_id: int,
        existing_row: Dict[str, Any],
        customer_payload: Dict[str, Optional[str]],
        tg_chat_id: str,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"id": customer_id}

        desired_first_name = cls._normalize_text_value(customer_payload.get("first_name"))
        current_first_name = cls._normalize_text_value(existing_row.get("first_name"))
        if desired_first_name and desired_first_name != current_first_name:
            payload["first_name"] = desired_first_name

        desired_last_name = cls._normalize_text_value(customer_payload.get("last_name"))
        current_last_name = cls._normalize_text_value(existing_row.get("last_name"))
        if desired_last_name and desired_last_name != current_last_name:
            payload["last_name"] = desired_last_name

        desired_full_name = cls._normalize_text_value(customer_payload.get("full_name"))
        current_full_name = cls._normalize_text_value(existing_row.get("full_name"))
        if desired_full_name and desired_full_name != current_full_name:
            payload["full_name"] = desired_full_name

        desired_phone = _normalize_phone(customer_payload.get("main_phone"))
        current_phone = _normalize_phone(existing_row.get("main_phone"))
        if desired_phone and desired_phone != current_phone:
            payload["main_phone"] = desired_phone

        desired_telegram_id = str(tg_chat_id)
        current_telegram_id = cls._extract_field_value(
            existing_row.get("fields"), "field_telegram_id"
        )
        if current_telegram_id != desired_telegram_id:
            payload["fields"] = [{"key": "field_telegram_id", "value": desired_telegram_id}]

        return payload

    @classmethod
    async def _edit_retail_customer_if_needed(
        cls,
        connected_integration_id: str,
        customer_id: int,
        existing_row: Dict[str, Any],
        customer_payload: Dict[str, Optional[str]],
        tg_chat_id: str,
    ) -> bool:
        edit_payload = cls._build_retail_customer_edit_payload(
            customer_id=customer_id,
            existing_row=existing_row,
            customer_payload=customer_payload,
            tg_chat_id=tg_chat_id,
        )
        if sorted(edit_payload.keys()) == ["id"]:
            return False

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            resp = await api.call(
                "RetailCustomer/Edit",
                edit_payload,
                APIBaseResponse[Dict[str, Any]],
            )
        if not resp.ok:
            logger.warning(
                "RetailCustomer/Edit rejected during auto-contact update: ci=%s customer_id=%s payload=%s result=%s",
                connected_integration_id,
                customer_id,
                edit_payload,
                resp.result,
            )
            return False
        return True

    @classmethod
    async def _ensure_retail_customer_contact(
        cls,
        connected_integration_id: str,
        bot_cfg: BotSlotConfig,
        tg_chat_id: str,
        message: Dict[str, Any],
    ) -> Tuple[Optional[int], str, Optional[str], Optional[bool]]:
        mapping_key = cls._retail_customer_by_tg_key(
            connected_integration_id, bot_cfg.bot_hash, tg_chat_id
        )
        cached_raw = await cls._redis_get(mapping_key)
        cached_id = _parse_int(cached_raw)
        if cached_id and cached_id > 0:
            return (
                cached_id,
                TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_REUSED,
                None,
                None,
            )

        customer_payload = cls._build_retail_customer_payload(message, tg_chat_id)
        customer_name = cls._retail_customer_name(customer_payload, tg_chat_id)
        group_id = bot_cfg.retail_customer_group_id
        if not group_id:
            logger.warning(
                "Auto-contact create skipped: ci=%s bot_hash=%s tg_chat_id=%s reason=group_id_not_configured",
                connected_integration_id,
                bot_cfg.bot_hash,
                tg_chat_id,
            )
            return None, TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_NONE, None, None

        existing_customer_row = await cls._find_existing_retail_customer(
            connected_integration_id=connected_integration_id,
            tg_chat_id=tg_chat_id,
        )
        existing_customer_id = (
            _parse_int(str(existing_customer_row.get("id") or ""))
            if isinstance(existing_customer_row, dict)
            else None
        )
        if existing_customer_id and existing_customer_id > 0:
            existing_has_phone = bool(
                _normalize_phone(
                    customer_payload.get("main_phone")
                    or (existing_customer_row or {}).get("main_phone")
                )
            )
            was_updated = await cls._edit_retail_customer_if_needed(
                connected_integration_id=connected_integration_id,
                customer_id=existing_customer_id,
                existing_row=existing_customer_row,
                customer_payload=customer_payload,
                tg_chat_id=tg_chat_id,
            )
            await cls._redis_set_mapping(mapping_key, str(existing_customer_id))
            logger.debug(
                "Auto-contact existing customer handled: ci=%s bot_hash=%s tg_chat_id=%s customer_id=%s updated=%s",
                connected_integration_id,
                bot_cfg.bot_hash,
                tg_chat_id,
                existing_customer_id,
                was_updated,
            )
            return (
                existing_customer_id,
                (
                    TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_UPDATED
                    if was_updated
                    else TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_REUSED
                ),
                customer_name,
                existing_has_phone,
            )

        main_phone = customer_payload.get("main_phone")
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            resp = await api.call(
                "RetailCustomer/Add",
                {
                    "group_id": group_id,
                    "first_name": str(customer_payload.get("first_name") or tg_chat_id),
                    "last_name": customer_payload.get("last_name"),
                    "full_name": customer_payload.get("full_name"),
                    "main_phone": main_phone,
                    "fields": [{"key": "field_telegram_id", "value": str(tg_chat_id)}],
                },
                APIBaseResponse[Dict[str, Any]],
            )
        if not resp.ok:
            logger.warning(
                "RetailCustomer/Add rejected during auto-contact create: ci=%s bot_hash=%s tg_chat_id=%s payload=%s",
                connected_integration_id,
                bot_cfg.bot_hash,
                tg_chat_id,
                resp.result,
            )
            return None, TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_NONE, None, None

        customer_id = (
            _parse_int(str(resp.result.get("new_id") or ""))
            if isinstance(resp.result, dict)
            else None
        )
        if not customer_id or customer_id <= 0:
            logger.warning(
                "RetailCustomer/Add returned empty new_id: ci=%s bot_hash=%s tg_chat_id=%s payload=%s",
                connected_integration_id,
                bot_cfg.bot_hash,
                tg_chat_id,
                resp.result,
            )
            return None, TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_NONE, None, None

        await cls._redis_set_mapping(mapping_key, str(customer_id))
        logger.debug(
            "Auto-contact created: ci=%s bot_hash=%s tg_chat_id=%s customer_id=%s group_id=%s has_phone=%s",
            connected_integration_id,
            bot_cfg.bot_hash,
            tg_chat_id,
            customer_id,
            group_id,
            bool(main_phone),
        )
        return (
            customer_id,
            TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_CREATED,
            customer_name,
            bool(_normalize_phone(main_phone)),
        )

    @classmethod
    async def _ensure_auto_contact_best_effort(
        cls,
        connected_integration_id: str,
        bot_cfg: BotSlotConfig,
        tg_chat_id: str,
        message: Dict[str, Any],
    ) -> Tuple[Optional[int], str, Optional[str], Optional[bool]]:
        if (
            bot_cfg.auto_create_contact_mode
            != TelegramBotCrmChannelConfig.AUTO_CREATE_CONTACT_RETAIL_CUSTOMER
        ):
            return None, TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_NONE, None, None

        try:
            return await cls._ensure_retail_customer_contact(
                connected_integration_id=connected_integration_id,
                bot_cfg=bot_cfg,
                tg_chat_id=tg_chat_id,
                message=message,
            )
        except Exception as error:
            logger.warning(
                "Auto-contact create failed: ci=%s bot_hash=%s tg_chat_id=%s error=%s",
                connected_integration_id,
                bot_cfg.bot_hash,
                tg_chat_id,
                error,
            )
            return None, TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_NONE, None, None

    @classmethod
    async def _send_retail_customer_system_message_best_effort(
        cls,
        connected_integration_id: str,
        chat_id: str,
        bot_hash: str,
        tg_chat_id: str,
        customer_id: int,
        action: str,
        customer_name: Optional[str],
    ) -> None:
        if not chat_id or not customer_id:
            return
        if action == TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_CREATED:
            text = TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_CREATED_TEXT.format(
                name=customer_name or tg_chat_id
            )
        elif action == TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_UPDATED:
            text = TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_UPDATED_TEXT.format(
                name=customer_name or tg_chat_id
            )
        else:
            return
        external_message_id = (
            f"tgsys:retail_customer_{action}:{bot_hash}:{tg_chat_id}:{customer_id}"
        )
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                response = await api.call(
                    "ChatMessage/Add",
                    {
                        "chat_id": chat_id,
                        "message_type": ChatMessageTypeEnum.System.value,
                        "text": text,
                        "external_message_id": external_message_id,
                    },
                    APIBaseResponse[Dict[str, Any]],
                )
            if not response.ok:
                logger.warning(
                    "Retail-customer system message rejected: ci=%s chat_id=%s customer_id=%s action=%s payload=%s",
                    connected_integration_id,
                    chat_id,
                    customer_id,
                    action,
                    response.result,
                )
        except Exception as error:
            logger.warning(
                "Failed to send retail-customer system message: ci=%s chat_id=%s customer_id=%s action=%s error=%s",
                connected_integration_id,
                chat_id,
                customer_id,
                action,
                error,
            )

    @classmethod
    async def _send_phone_system_message_best_effort(
        cls,
        connected_integration_id: str,
        chat_id: str,
        external_message_id: str,
        text: str,
    ) -> None:
        if not chat_id or not text:
            return
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                response = await api.call(
                    "ChatMessage/Add",
                    {
                        "chat_id": chat_id,
                        "message_type": ChatMessageTypeEnum.System.value,
                        "text": str(text),
                        "external_message_id": str(external_message_id),
                    },
                    APIBaseResponse[Dict[str, Any]],
                )
            if not response.ok:
                logger.warning(
                    "Phone-flow system message rejected: ci=%s chat_id=%s external_message_id=%s payload=%s",
                    connected_integration_id,
                    chat_id,
                    external_message_id,
                    response.result,
                )
        except Exception as error:
            logger.warning(
                "Failed to send phone-flow system message: ci=%s chat_id=%s external_message_id=%s error=%s",
                connected_integration_id,
                chat_id,
                external_message_id,
                error,
            )

    @classmethod
    async def _resolve_client_photo_url(
        cls, bot_cfg: BotSlotConfig, message: Dict[str, Any]
    ) -> Optional[str]:
        chat = message.get("chat")
        chat = chat if isinstance(chat, dict) else {}
        sender_business_bot = message.get("sender_business_bot")
        sender_chat = message.get("sender_chat")
        is_from_offline = bool(message.get("is_from_offline"))
        user_id_int, user_id_source = _resolve_avatar_user_id(message)
        chat_id_int = _parse_int(str(chat.get("id") or ""), None)
        chat_type = str(chat.get("type") or "").strip().lower()
        private_chat_id = (
            int(chat_id_int)
            if chat_type == "private" and chat_id_int and chat_id_int > 0
            else None
        )

        if not user_id_int and not private_chat_id:
            if isinstance(sender_business_bot, dict):
                logger.debug(
                    "Avatar resolve skipped: bot_hash=%s reason=outgoing_business_message",
                    bot_cfg.bot_hash,
                )
                return None
            if isinstance(sender_chat, dict):
                logger.debug(
                    "Avatar resolve skipped: bot_hash=%s reason=sender_chat_only",
                    bot_cfg.bot_hash,
                )
                return None
            if is_from_offline:
                logger.debug(
                    "Avatar resolve skipped: bot_hash=%s reason=offline_implicit_message",
                    bot_cfg.bot_hash,
                )
                return None
            logger.debug(
                "Avatar resolve skipped: bot_hash=%s reason=no_user_id",
                bot_cfg.bot_hash,
            )
            return None

        try:
            logger.debug(
                "Avatar resolve started: bot_hash=%s tg_user_id=%s user_source=%s tg_chat_id=%s chat_type=%s",
                bot_cfg.bot_hash,
                user_id_int,
                user_id_source,
                private_chat_id,
                chat_type or "unknown",
            )
            bot = await cls._get_bot(bot_cfg.token)

            avatar_file_id: Optional[str] = None
            avatar_source = "none"

            if user_id_int:
                try:
                    photos = await bot.get_user_profile_photos(user_id=user_id_int, limit=1)
                    rows = photos.photos[0] if photos and photos.photos else []
                    if rows:
                        best = max(
                            [row for row in rows if getattr(row, "file_id", None)],
                            key=lambda row: int(getattr(row, "file_size", 0) or 0),
                            default=None,
                        )
                        if best and getattr(best, "file_id", None):
                            avatar_file_id = str(best.file_id).strip()
                            avatar_source = "user_profile_photos"
                        else:
                            logger.debug(
                                "Avatar resolve user lookup result: bot_hash=%s tg_user_id=%s status=no_file_id",
                                bot_cfg.bot_hash,
                                user_id_int,
                            )
                    else:
                        logger.debug(
                            "Avatar resolve user lookup result: bot_hash=%s tg_user_id=%s status=no_photos",
                            bot_cfg.bot_hash,
                            user_id_int,
                        )
                except Exception as error:
                    logger.debug(
                        "Avatar resolve user lookup failed: bot_hash=%s tg_user_id=%s error=%s",
                        bot_cfg.bot_hash,
                        user_id_int,
                        error,
                    )

            if not avatar_file_id and private_chat_id:
                try:
                    chat_info = await bot.get_chat(chat_id=private_chat_id)
                    chat_photo = getattr(chat_info, "photo", None)
                    chat_file_id = str(
                        getattr(chat_photo, "big_file_id", None)
                        or getattr(chat_photo, "small_file_id", None)
                        or ""
                    ).strip()
                    if chat_file_id:
                        avatar_file_id = chat_file_id
                        avatar_source = "chat_photo"
                    else:
                        logger.debug(
                            "Avatar resolve chat lookup result: bot_hash=%s tg_chat_id=%s status=no_chat_photo",
                            bot_cfg.bot_hash,
                            private_chat_id,
                        )
                except Exception as error:
                    logger.debug(
                        "Avatar resolve chat lookup failed: bot_hash=%s tg_chat_id=%s error=%s",
                        bot_cfg.bot_hash,
                        private_chat_id,
                        error,
                    )

            if not avatar_file_id:
                logger.debug(
                    "Avatar resolve result: bot_hash=%s tg_user_id=%s tg_chat_id=%s status=not_found",
                    bot_cfg.bot_hash,
                    user_id_int,
                    private_chat_id,
                )
                return None

            file_info = await bot.get_file(avatar_file_id)
            file_path = str(file_info.file_path or "").strip()
            if not file_path:
                logger.debug(
                    "Avatar resolve result: bot_hash=%s tg_user_id=%s tg_chat_id=%s source=%s status=no_file_path file_id=%s",
                    bot_cfg.bot_hash,
                    user_id_int,
                    private_chat_id,
                    avatar_source,
                    avatar_file_id,
                )
                return None
            logger.debug(
                "Avatar resolve success: bot_hash=%s tg_user_id=%s tg_chat_id=%s source=%s file_id=%s file_path=%s",
                bot_cfg.bot_hash,
                user_id_int,
                private_chat_id,
                avatar_source,
                avatar_file_id,
                file_path,
            )
            return f"https://api.telegram.org/file/bot{bot_cfg.token}/{file_path}"
        except Exception as error:
            logger.debug(
                "Avatar resolve failed: bot_hash=%s tg_user_id=%s tg_chat_id=%s error=%s",
                bot_cfg.bot_hash,
                user_id_int,
                private_chat_id,
                error,
            )
            return None

    @staticmethod
    def _normalize_text_value(value: Any) -> Optional[str]:
        text = str(value or "").strip()
        return text or None

    @classmethod
    def _build_lead_contact_payload(
        cls,
        bot_cfg: BotSlotConfig,
        message: Dict[str, Any],
        tg_chat_id: str,
    ) -> Dict[str, Optional[str]]:
        contact_payload = cls._extract_contact_payload(message, tg_chat_id)
        client_name = cls._normalize_text_value(contact_payload.get("display_name"))
        subject = cls._normalize_text_value(
            cls._build_subject(bot_cfg.lead_subject_template, message, tg_chat_id)
        )

        client_phone = cls._normalize_text_value(cls._extract_own_contact_phone(message))

        return {
            "subject": subject,
            "external_id": _lead_external_id(bot_cfg.bot_hash, tg_chat_id),
            "client_name": client_name,
            "client_phone": client_phone,
        }

    @classmethod
    def _build_lead_sync_patch(
        cls,
        lead: Lead,
        desired_payload: Dict[str, Optional[str]],
    ) -> Dict[str, str]:
        patch: Dict[str, str] = {}
        field_names = [
            "subject",
            "external_id",
            "client_name",
            "client_phone",
        ]
        for field_name in field_names:
            desired_value = cls._normalize_text_value(desired_payload.get(field_name))
            if not desired_value:
                continue
            current_value = cls._normalize_text_value(getattr(lead, field_name, None))
            if current_value != desired_value:
                patch[field_name] = desired_value
        return patch

    @classmethod
    def _build_lead_sync_patch_from_cached(
        cls,
        desired_payload: Dict[str, Optional[str]],
        cached_payload: Dict[str, Any],
    ) -> Dict[str, str]:
        patch: Dict[str, str] = {}
        field_names = [
            "subject",
            "external_id",
            "client_name",
            "client_phone",
        ]
        for field_name in field_names:
            desired_value = cls._normalize_text_value(desired_payload.get(field_name))
            if not desired_value:
                continue
            cached_value = cls._normalize_text_value(cached_payload.get(field_name))
            if cached_value != desired_value:
                patch[field_name] = desired_value
        return patch

    @staticmethod
    def _parse_lead_sync_cache(raw: Optional[str]) -> Optional[Dict[str, Any]]:
        if not raw:
            return None
        try:
            payload = _json_loads(raw)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    @classmethod
    def _build_lead_sync_cache_payload(
        cls,
        desired_payload: Dict[str, Optional[str]],
        *,
        avatar_state: str,
        avatar_url: Optional[str],
        avatar_check_after_ts: int,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        field_names = [
            "subject",
            "external_id",
            "client_name",
            "client_phone",
        ]
        for field_name in field_names:
            payload[field_name] = cls._normalize_text_value(desired_payload.get(field_name)) or ""

        normalized_avatar_state = str(avatar_state or "").strip().lower()
        payload["avatar_state"] = "present" if normalized_avatar_state == "present" else "missing"
        payload["client_photo_url"] = cls._normalize_text_value(avatar_url) or ""
        payload["avatar_check_after_ts"] = max(avatar_check_after_ts, 0)
        return payload

    @classmethod
    async def _sync_lead_from_telegram_best_effort(
        cls,
        connected_integration_id: str,
        state_ttl_sec: int,
        bot_cfg: BotSlotConfig,
        lead_id: int,
        tg_chat_id: str,
        message: Dict[str, Any],
    ) -> None:
        desired_payload = cls._build_lead_contact_payload(bot_cfg, message, tg_chat_id)
        cache_key = cls._lead_sync_cache_key(connected_integration_id, lead_id)
        now_ts = _now_ts()
        avatar_recheck_sec = max(
            min(state_ttl_sec, TelegramBotCrmChannelConfig.LEAD_SYNC_AVATAR_RECHECK_SEC),
            300,
        )
        avatar_fast_recheck_sec = min(avatar_recheck_sec, 300)

        cached_payload_raw = await cls._redis_get(cache_key)
        cached_payload = cls._parse_lead_sync_cache(cached_payload_raw)
        logger.debug(
            "Lead sync started: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s cache_hit=%s",
            connected_integration_id,
            lead_id,
            bot_cfg.bot_hash,
            tg_chat_id,
            bool(cached_payload),
        )

        if cached_payload:
            patch = cls._build_lead_sync_patch_from_cached(desired_payload, cached_payload)

            cached_avatar_state = str(cached_payload.get("avatar_state") or "").strip().lower()
            cached_avatar_url = cls._normalize_text_value(cached_payload.get("client_photo_url"))
            cached_avatar_check_after_ts = (
                _parse_int(str(cached_payload.get("avatar_check_after_ts") or ""), 0) or 0
            )
            has_avatar_user_hint = _message_has_avatar_user_hint(message)
            retry_in_sec = max(cached_avatar_check_after_ts - now_ts, 0)
            early_retry = (
                cached_avatar_state != "present"
                and has_avatar_user_hint
                and retry_in_sec > avatar_fast_recheck_sec
            )
            avatar_check_due = (
                cached_avatar_state != "present"
                and (now_ts >= cached_avatar_check_after_ts or early_retry)
            )
            logger.debug(
                "Lead sync cache state: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s avatar_state=%s avatar_check_due=%s early_retry=%s has_avatar_user_hint=%s patch_keys=%s",
                connected_integration_id,
                lead_id,
                bot_cfg.bot_hash,
                tg_chat_id,
                cached_avatar_state or "missing",
                avatar_check_due,
                early_retry,
                has_avatar_user_hint,
                sorted(patch.keys()),
            )

            avatar_state = "present" if cached_avatar_state == "present" else "missing"
            avatar_url = cached_avatar_url
            avatar_check_after_ts = (
                now_ts + avatar_recheck_sec
                if avatar_state != "present"
                else now_ts + state_ttl_sec
            )

            if avatar_check_due:
                resolved_avatar_url = await cls._resolve_client_photo_url(bot_cfg, message)
                if resolved_avatar_url:
                    normalized_resolved = cls._normalize_text_value(resolved_avatar_url)
                    if normalized_resolved and normalized_resolved != cached_avatar_url:
                        patch["client_photo_url"] = normalized_resolved
                        logger.debug(
                            "Lead sync avatar patch prepared: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s",
                            connected_integration_id,
                            lead_id,
                            bot_cfg.bot_hash,
                            tg_chat_id,
                        )
                    avatar_state = "present"
                    avatar_url = normalized_resolved
                    avatar_check_after_ts = now_ts + state_ttl_sec
                    logger.debug(
                        "Lead sync avatar recheck result: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s status=resolved",
                        connected_integration_id,
                        lead_id,
                        bot_cfg.bot_hash,
                        tg_chat_id,
                    )
                else:
                    avatar_state = "missing"
                    avatar_check_after_ts = (
                        now_ts + avatar_fast_recheck_sec
                        if has_avatar_user_hint
                        else now_ts + avatar_recheck_sec
                    )
                    logger.debug(
                        "Lead sync avatar recheck result: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s status=not_found",
                        connected_integration_id,
                        lead_id,
                        bot_cfg.bot_hash,
                        tg_chat_id,
                    )

            if not patch:
                logger.debug(
                    "Lead sync skipped (no changes): ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s",
                    connected_integration_id,
                    lead_id,
                    bot_cfg.bot_hash,
                    tg_chat_id,
                )
                if avatar_check_due:
                    await cls._redis_set_with_ttl(
                        cache_key,
                        _json_dumps(
                            cls._build_lead_sync_cache_payload(
                                desired_payload,
                                avatar_state=avatar_state,
                                avatar_url=avatar_url,
                                avatar_check_after_ts=avatar_check_after_ts,
                            )
                        ),
                        state_ttl_sec,
                    )
                return

            try:
                logger.debug(
                    "Lead sync editing from cache: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s patch_keys=%s has_avatar_patch=%s",
                    connected_integration_id,
                    lead_id,
                    bot_cfg.bot_hash,
                    tg_chat_id,
                    sorted(patch.keys()),
                    "client_photo_url" in patch,
                )
                async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                    response = await api.crm.lead.edit(LeadEditRequest(id=lead_id, **patch))
                if response.ok:
                    if "client_photo_url" in patch:
                        avatar_state = "present"
                        avatar_url = cls._normalize_text_value(patch.get("client_photo_url"))
                        avatar_check_after_ts = now_ts + state_ttl_sec
                    await cls._redis_set_with_ttl(
                        cache_key,
                        _json_dumps(
                            cls._build_lead_sync_cache_payload(
                                desired_payload,
                                avatar_state=avatar_state,
                                avatar_url=avatar_url,
                                avatar_check_after_ts=avatar_check_after_ts,
                            )
                        ),
                        state_ttl_sec,
                    )
                    logger.debug(
                        "Lead sync edit accepted: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s patch_keys=%s",
                        connected_integration_id,
                        lead_id,
                        bot_cfg.bot_hash,
                        tg_chat_id,
                        sorted(patch.keys()),
                    )
                    return

                payload = response.result if isinstance(response.result, dict) else {}
                logger.warning(
                    "Lead/Edit rejected while syncing Telegram profile: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s error=%s description=%s",
                    connected_integration_id,
                    lead_id,
                    bot_cfg.bot_hash,
                    tg_chat_id,
                    payload.get("error"),
                    payload.get("description"),
                )
                return
            except Exception as error:
                logger.warning(
                    "Lead sync from Telegram failed: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s error=%s",
                    connected_integration_id,
                    lead_id,
                    bot_cfg.bot_hash,
                    tg_chat_id,
                    error,
                )
                return

        try:
            logger.debug(
                "Lead sync cache miss -> loading lead: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s",
                connected_integration_id,
                lead_id,
                bot_cfg.bot_hash,
                tg_chat_id,
            )
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                lead = await api.crm.lead.get_by_id(lead_id)
                if not lead:
                    logger.debug(
                        "Lead sync stopped: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s reason=lead_not_found",
                        connected_integration_id,
                        lead_id,
                        bot_cfg.bot_hash,
                        tg_chat_id,
                    )
                    return

                patch = cls._build_lead_sync_patch(lead, desired_payload)
                avatar_url = cls._normalize_text_value(lead.client_photo_url)
                avatar_state = "present" if avatar_url else "missing"
                avatar_check_after_ts = (
                    now_ts + state_ttl_sec
                    if avatar_state == "present"
                    else now_ts + avatar_recheck_sec
                )

                if avatar_state != "present":
                    logger.debug(
                        "Lead sync avatar missing in lead: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s",
                        connected_integration_id,
                        lead_id,
                        bot_cfg.bot_hash,
                        tg_chat_id,
                    )
                    avatar_url = await cls._resolve_client_photo_url(bot_cfg, message)
                    if avatar_url:
                        patch["client_photo_url"] = avatar_url
                        avatar_state = "present"
                        avatar_check_after_ts = now_ts + state_ttl_sec
                        logger.debug(
                            "Lead sync avatar patch prepared from fresh lead: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s",
                            connected_integration_id,
                            lead_id,
                            bot_cfg.bot_hash,
                            tg_chat_id,
                        )
                    else:
                        logger.debug(
                            "Lead sync avatar still missing after Telegram lookup: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s",
                            connected_integration_id,
                            lead_id,
                            bot_cfg.bot_hash,
                            tg_chat_id,
                        )

                if not patch:
                    logger.debug(
                        "Lead sync skipped after fresh lead load (no changes): ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s",
                        connected_integration_id,
                        lead_id,
                        bot_cfg.bot_hash,
                        tg_chat_id,
                    )
                    await cls._redis_set_with_ttl(
                        cache_key,
                        _json_dumps(
                            cls._build_lead_sync_cache_payload(
                                desired_payload,
                                avatar_state=avatar_state,
                                avatar_url=avatar_url,
                                avatar_check_after_ts=avatar_check_after_ts,
                            )
                        ),
                        state_ttl_sec,
                    )
                    return

                logger.debug(
                    "Lead sync editing after fresh lead load: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s patch_keys=%s has_avatar_patch=%s",
                    connected_integration_id,
                    lead_id,
                    bot_cfg.bot_hash,
                    tg_chat_id,
                    sorted(patch.keys()),
                    "client_photo_url" in patch,
                )
                response = await api.crm.lead.edit(LeadEditRequest(id=lead_id, **patch))
                if response.ok:
                    if "client_photo_url" in patch:
                        avatar_state = "present"
                        avatar_url = cls._normalize_text_value(patch.get("client_photo_url"))
                        avatar_check_after_ts = now_ts + state_ttl_sec
                    await cls._redis_set_with_ttl(
                        cache_key,
                        _json_dumps(
                            cls._build_lead_sync_cache_payload(
                                desired_payload,
                                avatar_state=avatar_state,
                                avatar_url=avatar_url,
                                avatar_check_after_ts=avatar_check_after_ts,
                            )
                        ),
                        state_ttl_sec,
                    )
                    logger.debug(
                        "Lead sync edit accepted: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s patch_keys=%s",
                        connected_integration_id,
                        lead_id,
                        bot_cfg.bot_hash,
                        tg_chat_id,
                        sorted(patch.keys()),
                    )
                    return

                payload = response.result if isinstance(response.result, dict) else {}
                logger.warning(
                    "Lead/Edit rejected while syncing Telegram profile: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s error=%s description=%s",
                    connected_integration_id,
                    lead_id,
                    bot_cfg.bot_hash,
                    tg_chat_id,
                    payload.get("error"),
                    payload.get("description"),
                )
        except Exception as error:
            logger.warning(
                "Lead sync from Telegram failed: ci=%s lead_id=%s bot_hash=%s tg_chat_id=%s error=%s",
                connected_integration_id,
                lead_id,
                bot_cfg.bot_hash,
                tg_chat_id,
                error,
            )

    @classmethod
    async def _set_worker_heartbeat(cls, connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        await redis_client.setex(
            cls._worker_heartbeat_key(connected_integration_id), 30, str(_now_ts())
        )

    @classmethod
    async def _stream_worker_loop(cls, connected_integration_id: str, kind: str) -> None:
        stream_key = cls._stream_key(kind, connected_integration_id)
        consumer = f"{_INSTANCE_ID}:{kind}"
        await cls._ensure_consumer_group(stream_key)
        logger.info("Stream worker started for %s (%s)", connected_integration_id, kind)

        while True:
            try:
                await cls._set_worker_heartbeat(connected_integration_id)
                await cls._process_claimed_entries(
                    stream_key, consumer, connected_integration_id, kind
                )
                try:
                    records = await redis_client.xreadgroup(
                        groupname=TelegramBotCrmChannelConfig.STREAM_GROUP,
                        consumername=consumer,
                        streams={stream_key: ">"},
                        count=TelegramBotCrmChannelConfig.STREAM_BATCH_SIZE,
                        block=TelegramBotCrmChannelConfig.STREAM_READ_BLOCK_MS,
                    )
                except Exception as error:
                    if _is_redis_nogroup_error(error):
                        await cls._ensure_consumer_group(stream_key)
                        logger.warning(
                            "Recovered missing Redis stream/group after NOGROUP: ci=%s kind=%s stream=%s op=xreadgroup",
                            connected_integration_id,
                            kind,
                            stream_key,
                        )
                        await asyncio.sleep(0.1)
                        continue
                    raise
                if not records:
                    continue

                for _, entries in records:
                    for message_id, fields in entries:
                        await cls._process_stream_entry(
                            stream_key=stream_key,
                            message_id=message_id,
                            fields=fields,
                            connected_integration_id=connected_integration_id,
                            kind=kind,
                        )
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.exception(
                    "Stream worker error for %s (%s): %s",
                    connected_integration_id,
                    kind,
                    error,
                )
                await asyncio.sleep(1.0)

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
        connected_integration_id: str,
        kind: str,
    ) -> None:
        try:
            claimed_raw = await redis_client.xautoclaim(
                stream_key,
                TelegramBotCrmChannelConfig.STREAM_GROUP,
                consumer,
                min_idle_time=TelegramBotCrmChannelConfig.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=TelegramBotCrmChannelConfig.STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if _is_redis_nogroup_error(error):
                await cls._ensure_consumer_group(stream_key)
                logger.warning(
                    "Recovered missing Redis stream/group after NOGROUP: ci=%s kind=%s stream=%s op=xautoclaim",
                    connected_integration_id,
                    kind,
                    stream_key,
                )
                return
            raise
        entries = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []
        for message_id, fields in entries:
            await cls._process_stream_entry(
                stream_key=stream_key,
                message_id=message_id,
                fields=fields,
                connected_integration_id=connected_integration_id,
                kind=kind,
            )

    @classmethod
    async def _process_stream_entry(
        cls,
        stream_key: str,
        message_id: str,
        fields: Dict[str, str],
        connected_integration_id: str,
        kind: str,
    ) -> None:
        attempts = int(str(fields.get("attempt") or "0"))
        try:
            if kind == "telegram_in":
                await cls._process_telegram_event(connected_integration_id, fields)
            else:
                await cls._process_regos_event(connected_integration_id, fields)
            await redis_client.xack(
                stream_key, TelegramBotCrmChannelConfig.STREAM_GROUP, message_id
            )
            logger.debug(
                "stream ack: ci=%s kind=%s message_id=%s",
                connected_integration_id,
                kind,
                message_id,
            )
        except Exception as error:
            attempts += 1
            if attempts >= TelegramBotCrmChannelConfig.STREAM_MAX_RETRIES:
                dlq_payload = dict(fields)
                dlq_payload["error"] = str(error)
                dlq_payload["attempt"] = str(attempts)
                dlq_payload["source_stream"] = stream_key
                dlq_payload["source_message_id"] = message_id
                await cls._enqueue(cls._dlq_stream_key(connected_integration_id), dlq_payload)
                if kind == "regos_in":
                    await cls._notify_telegram_delivery_issue_best_effort(
                        connected_integration_id=connected_integration_id,
                        fields=fields,
                        error_text=str(error),
                    )
                await redis_client.xack(
                    stream_key, TelegramBotCrmChannelConfig.STREAM_GROUP, message_id
                )
                logger.error(
                    "Moved message to DLQ: ci=%s kind=%s message_id=%s error=%s",
                    connected_integration_id,
                    kind,
                    message_id,
                    error,
                )
                return

            retry_payload = dict(fields)
            retry_payload["attempt"] = str(attempts)
            retry_payload["last_error"] = str(error)
            await cls._enqueue(stream_key, retry_payload)
            await redis_client.xack(
                stream_key, TelegramBotCrmChannelConfig.STREAM_GROUP, message_id
            )
            logger.warning(
                "Requeued stream event: ci=%s kind=%s attempt=%s message_id=%s error=%s",
                connected_integration_id,
                kind,
                attempts,
                message_id,
                error,
            )

    @classmethod
    async def _polling_loop(
        cls, connected_integration_id: str, bot_config: BotSlotConfig
    ) -> None:
        bot = await cls._get_bot(bot_config.token)
        offset: Optional[int] = None
        lock_key = cls._lock_polling_owner_key(bot_config.bot_hash)
        owner = _INSTANCE_ID
        logger.info(
            "Longpolling worker started for bot_hash=%s ci=%s",
            bot_config.bot_hash,
            connected_integration_id,
        )

        try:
            while True:
                try:
                    acquired = await redis_client.set(
                        lock_key,
                        owner,
                        ex=TelegramBotCrmChannelConfig.POLLING_LOCK_TTL_SEC,
                        nx=True,
                    )
                    if not acquired:
                        current_owner = await redis_client.get(lock_key)
                        if current_owner == owner:
                            await redis_client.expire(
                                lock_key, TelegramBotCrmChannelConfig.POLLING_LOCK_TTL_SEC
                            )
                            acquired = True

                    if not acquired:
                        await asyncio.sleep(1.5)
                        continue

                    updates = await bot.get_updates(
                        offset=offset,
                        timeout=20,
                        allowed_updates=[
                            "message",
                            "business_message",
                            "edited_message",
                            "edited_business_message",
                            "deleted_business_messages",
                        ],
                    )
                    if not updates:
                        await asyncio.sleep(0.1)
                        continue

                    for update in updates:
                        offset = int(update.update_id) + 1
                        await cls._enqueue(
                            cls._stream_key("telegram_in", connected_integration_id),
                            {
                                "connected_integration_id": connected_integration_id,
                                "bot_hash": bot_config.bot_hash,
                                "payload": update.model_dump(mode="json", by_alias=True),
                                "attempt": "0",
                                "enqueued_at": str(_now_ts()),
                            },
                        )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.warning(
                        "Polling loop transient error for bot_hash=%s ci=%s: %s",
                        bot_config.bot_hash,
                        connected_integration_id,
                        error,
                    )
                    await asyncio.sleep(1.5)
        except asyncio.CancelledError:
            raise
        finally:
            await cls._release_lock(lock_key, owner)

    @classmethod
    async def _process_telegram_event(
        cls, connected_integration_id: str, fields: Dict[str, str]
    ) -> None:
        runtime = await cls._load_runtime(connected_integration_id)
        bot_hash = str(fields.get("bot_hash") or "").strip()
        if bot_hash not in runtime.bots_by_hash:
            logger.warning("Unknown bot_hash in Telegram stream: %s", bot_hash)
            return
        bot_cfg = runtime.bots_by_hash[bot_hash]

        payload_raw = fields.get("payload")
        payload = _json_loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        if not isinstance(payload, dict):
            return

        update_id = payload.get("update_id")
        if update_id is None:
            return
        try:
            update_id_int = int(update_id)
        except (TypeError, ValueError):
            return

        dedupe_key = cls._dedupe_tg_update_key(
            connected_integration_id, bot_hash, update_id_int
        )
        if await cls._redis_get(dedupe_key):
            return
        dedupe_lock_key = f"{dedupe_key}:lock"
        dedupe_lock_token = await cls._acquire_lock(dedupe_lock_key, 120)
        if not dedupe_lock_token:
            logger.debug(
                "Skip duplicate Telegram update (in-flight): ci=%s bot_hash=%s update_id=%s",
                connected_integration_id,
                bot_hash,
                update_id_int,
            )
            return

        try:
            if await cls._redis_get(dedupe_key):
                return

            message = payload.get("message")
            if not isinstance(message, dict):
                message = payload.get("business_message")
            if isinstance(message, dict):
                await cls._process_added_telegram_message(
                    connected_integration_id=connected_integration_id,
                    runtime=runtime,
                    bot_cfg=bot_cfg,
                    bot_hash=bot_hash,
                    message=message,
                )
                await cls._redis_set_with_ttl(dedupe_key, "1", runtime.lead_dedupe_ttl_sec)
                return

            edited_message = payload.get("edited_message")
            if not isinstance(edited_message, dict):
                edited_message = payload.get("edited_business_message")
            if isinstance(edited_message, dict):
                await cls._process_edited_telegram_message(
                    connected_integration_id=connected_integration_id,
                    runtime=runtime,
                    bot_cfg=bot_cfg,
                    bot_hash=bot_hash,
                    message=edited_message,
                )
                await cls._redis_set_with_ttl(dedupe_key, "1", runtime.lead_dedupe_ttl_sec)
                return

            deleted_rows = _extract_deleted_telegram_messages(payload)
            if deleted_rows:
                await cls._process_deleted_telegram_events(
                    connected_integration_id=connected_integration_id,
                    bot_cfg=bot_cfg,
                    bot_hash=bot_hash,
                    deleted_rows=deleted_rows,
                )
                await cls._redis_set_with_ttl(dedupe_key, "1", runtime.lead_dedupe_ttl_sec)
        finally:
            await cls._release_lock(dedupe_lock_key, dedupe_lock_token)

    @classmethod
    async def _process_added_telegram_message(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        bot_cfg: BotSlotConfig,
        bot_hash: str,
        message: Dict[str, Any],
    ) -> None:
        if isinstance(message.get("sender_business_bot"), dict):
            logger.debug(
                "Skip outbound business message in inbound add flow: ci=%s bot_hash=%s",
                connected_integration_id,
                bot_hash,
            )
            return

        author = cls._extract_message_author(message)
        if bool(author.get("is_bot")):
            return

        chat = message.get("chat") or {}
        tg_chat_id = str(chat.get("id") or "").strip()
        if not tg_chat_id:
            return

        lead_id, chat_id = await cls._resolve_or_create_lead(
            connected_integration_id=connected_integration_id,
            runtime=runtime,
            bot_cfg=bot_cfg,
            tg_chat_id=tg_chat_id,
            message=message,
        )
        if not lead_id or not chat_id:
            return

        # Contact creation is executed after lead resolution, so the same path
        # works for both newly created and already existing leads.
        (
            customer_id,
            customer_action,
            customer_name,
            retail_has_phone_hint,
        ) = await cls._ensure_auto_contact_best_effort(
            connected_integration_id=connected_integration_id,
            bot_cfg=bot_cfg,
            tg_chat_id=tg_chat_id,
            message=message,
        )
        if customer_id and customer_action in {
            TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_CREATED,
            TelegramBotCrmChannelConfig.RETAIL_CUSTOMER_ACTION_UPDATED,
        }:
            await cls._send_retail_customer_system_message_best_effort(
                connected_integration_id=connected_integration_id,
                chat_id=chat_id,
                bot_hash=bot_hash,
                tg_chat_id=tg_chat_id,
                customer_id=customer_id,
                action=customer_action,
                customer_name=customer_name,
            )

        await cls._sync_lead_from_telegram_best_effort(
            connected_integration_id=connected_integration_id,
            state_ttl_sec=runtime.state_ttl_sec,
            bot_cfg=bot_cfg,
            lead_id=lead_id,
            tg_chat_id=tg_chat_id,
            message=message,
        )

        try:
            await cls._maybe_request_phone_best_effort(
                connected_integration_id=connected_integration_id,
                runtime=runtime,
                bot_cfg=bot_cfg,
                lead_id=lead_id,
                chat_id=chat_id,
                tg_chat_id=tg_chat_id,
                message=message,
                customer_id=customer_id,
                retail_has_phone_hint=retail_has_phone_hint,
            )
        except Exception as error:
            logger.warning(
                "Phone request flow failed (ignored): ci=%s bot_hash=%s tg_chat_id=%s lead_id=%s error=%s",
                connected_integration_id,
                bot_hash,
                tg_chat_id,
                lead_id,
                error,
            )
        # Client wrote to the chat -> lead must be in active processing state.
        await cls._set_lead_status_best_effort(
            connected_integration_id=connected_integration_id,
            lead_id=lead_id,
            status=LeadStatusEnum.InProgress,
            reason="client_message",
        )

        await cls._mark_chat_read_best_effort(
            connected_integration_id=connected_integration_id,
            chat_id=chat_id,
        )

        text, file_ids = await cls._prepare_telegram_message_content(
            connected_integration_id=connected_integration_id,
            bot_cfg=bot_cfg,
            chat_id=chat_id,
            message=message,
        )
        if not text and not file_ids:
            return

        tg_message_id = _parse_int(str(message.get("message_id") or ""))
        if not tg_message_id:
            return

        try:
            await cls._add_or_get_regos_message_by_telegram(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_hash,
                tg_chat_id=tg_chat_id,
                tg_message_id=tg_message_id,
                lead_id=lead_id,
                chat_id=chat_id,
                text=text,
                file_ids=file_ids,
            )
            return
        except ChatMessageAddClosedEntityError as error:
            logger.info(
                "ChatMessage/Add rejected for closed linked entity. Retrying with a fresh lead: ci=%s bot_hash=%s tg_chat_id=%s old_lead_id=%s old_chat_id=%s error=%s",
                connected_integration_id,
                bot_hash,
                tg_chat_id,
                lead_id,
                chat_id,
                error,
            )

        fresh_lead_id, fresh_chat_id = await cls._resolve_or_create_lead(
            connected_integration_id=connected_integration_id,
            runtime=runtime,
            bot_cfg=bot_cfg,
            tg_chat_id=tg_chat_id,
            message=message,
        )
        if not fresh_lead_id or not fresh_chat_id:
            raise RuntimeError(
                "Failed to resolve fresh lead after ChatMessage/Add rejected for closed linked entity"
            )

        await cls._sync_lead_from_telegram_best_effort(
            connected_integration_id=connected_integration_id,
            state_ttl_sec=runtime.state_ttl_sec,
            bot_cfg=bot_cfg,
            lead_id=fresh_lead_id,
            tg_chat_id=tg_chat_id,
            message=message,
        )
        await cls._set_lead_status_best_effort(
            connected_integration_id=connected_integration_id,
            lead_id=fresh_lead_id,
            status=LeadStatusEnum.InProgress,
            reason="client_message",
        )
        await cls._mark_chat_read_best_effort(
            connected_integration_id=connected_integration_id,
            chat_id=fresh_chat_id,
        )

        fresh_text, fresh_file_ids = await cls._prepare_telegram_message_content(
            connected_integration_id=connected_integration_id,
            bot_cfg=bot_cfg,
            chat_id=fresh_chat_id,
            message=message,
        )
        if not fresh_text and not fresh_file_ids:
            return

        await cls._add_or_get_regos_message_by_telegram(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_hash,
            tg_chat_id=tg_chat_id,
            tg_message_id=tg_message_id,
            lead_id=fresh_lead_id,
            chat_id=fresh_chat_id,
            text=fresh_text,
            file_ids=fresh_file_ids,
        )

    @classmethod
    async def _process_edited_telegram_message(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        bot_cfg: BotSlotConfig,
        bot_hash: str,
        message: Dict[str, Any],
    ) -> None:
        if isinstance(message.get("sender_business_bot"), dict):
            logger.debug(
                "Skip outbound business message in inbound edit flow: ci=%s bot_hash=%s",
                connected_integration_id,
                bot_hash,
            )
            return

        author = cls._extract_message_author(message)
        if bool(author.get("is_bot")):
            return

        chat = message.get("chat") or {}
        tg_chat_id = str(chat.get("id") or "").strip()
        if not tg_chat_id:
            return

        tg_message_id = _parse_int(str(message.get("message_id") or ""))
        if not tg_message_id:
            return

        lead_id, chat_id = await cls._resolve_existing_lead(
            connected_integration_id=connected_integration_id,
            bot_cfg=bot_cfg,
            tg_chat_id=tg_chat_id,
        )
        if not lead_id or not chat_id:
            return

        await cls._sync_lead_from_telegram_best_effort(
            connected_integration_id=connected_integration_id,
            state_ttl_sec=runtime.state_ttl_sec,
            bot_cfg=bot_cfg,
            lead_id=lead_id,
            tg_chat_id=tg_chat_id,
            message=message,
        )

        await cls._mark_chat_read_best_effort(
            connected_integration_id=connected_integration_id,
            chat_id=chat_id,
        )

        text, file_ids = await cls._prepare_telegram_message_content(
            connected_integration_id=connected_integration_id,
            bot_cfg=bot_cfg,
            chat_id=chat_id,
            message=message,
        )
        if text is None and not file_ids:
            return

        regos_message_id = await cls._resolve_regos_message_id_by_tg(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_hash,
            tg_chat_id=tg_chat_id,
            tg_message_id=tg_message_id,
        )
        if not regos_message_id:
            regos_message_id = await cls._add_or_get_regos_message_by_telegram(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_hash,
                tg_chat_id=tg_chat_id,
                tg_message_id=tg_message_id,
                lead_id=lead_id,
                chat_id=chat_id,
                text=text,
                file_ids=file_ids,
            )
            if not regos_message_id:
                return

        await cls._edit_regos_message_from_telegram(
            connected_integration_id=connected_integration_id,
            regos_message_id=regos_message_id,
            text=text or "",
            file_ids=file_ids,
        )

    @classmethod
    async def _process_deleted_telegram_events(
        cls,
        connected_integration_id: str,
        bot_cfg: BotSlotConfig,
        bot_hash: str,
        deleted_rows: List[Tuple[str, int]],
    ) -> None:
        for tg_chat_id, tg_message_id in deleted_rows:
            regos_message_id = await cls._resolve_regos_message_id_by_tg(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_hash,
                tg_chat_id=tg_chat_id,
                tg_message_id=tg_message_id,
            )
            if not regos_message_id:
                _, chat_id = await cls._resolve_existing_lead(
                    connected_integration_id=connected_integration_id,
                    bot_cfg=bot_cfg,
                    tg_chat_id=tg_chat_id,
                )
                if chat_id:
                    regos_message_id = await cls._find_regos_message_id_by_external_id(
                        connected_integration_id=connected_integration_id,
                        chat_id=chat_id,
                        external_message_id=_tg_external_message_id(
                            bot_hash=bot_hash,
                            tg_chat_id=tg_chat_id,
                            tg_message_id=tg_message_id,
                        ),
                    )
                    if regos_message_id:
                        await cls._redis_set_mapping(
                            cls._msgmap_tg_to_regos_key(
                                connected_integration_id,
                                bot_hash,
                                tg_chat_id,
                                tg_message_id,
                            ),
                            regos_message_id,
                        )
            if not regos_message_id:
                logger.warning(
                    "Telegram delete skipped (mapping not found): ci=%s bot_hash=%s tg_chat_id=%s tg_message_id=%s",
                    connected_integration_id,
                    bot_hash,
                    tg_chat_id,
                    tg_message_id,
                )
                continue

            await cls._delete_regos_message_from_telegram(
                connected_integration_id=connected_integration_id,
                regos_message_id=regos_message_id,
            )
            await cls._redis_delete(
                cls._msgmap_tg_to_regos_key(
                    connected_integration_id, bot_hash, tg_chat_id, tg_message_id
                )
            )

    @classmethod
    async def _prepare_telegram_message_content(
        cls,
        connected_integration_id: str,
        bot_cfg: BotSlotConfig,
        chat_id: str,
        message: Dict[str, Any],
    ) -> Tuple[Optional[str], List[int]]:
        text = cls._telegram_message_to_crm_markdown(
            connected_integration_id=connected_integration_id,
            message=message,
        )
        file_ids, oversized_files_count = await cls._upload_telegram_files(
            connected_integration_id=connected_integration_id,
            bot_cfg=bot_cfg,
            chat_id=chat_id,
            message=message,
        )
        if oversized_files_count > 0:
            too_large_notice = (
                TelegramBotCrmChannelConfig.LARGE_FILE_NOTICE_TEXT
                if oversized_files_count == 1
                else TelegramBotCrmChannelConfig.LARGE_FILES_NOTICE_TEXT
            )
            text = f"{text}\n\n{too_large_notice}" if text else too_large_notice
        return text, file_ids

    @classmethod
    async def _resolve_regos_message_id_by_tg(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
        tg_message_id: int,
    ) -> Optional[str]:
        message_id = await cls._redis_get(
            cls._msgmap_tg_to_regos_key(
                connected_integration_id, bot_hash, tg_chat_id, tg_message_id
            )
        )
        resolved = str(message_id or "").strip()
        return resolved or None

    @classmethod
    async def _find_regos_message_id_by_external_id(
        cls,
        connected_integration_id: str,
        chat_id: str,
        external_message_id: str,
    ) -> Optional[str]:
        ext = str(external_message_id or "").strip()
        if not ext:
            return None

        offset = 0
        limit = 100
        scanned = 0
        max_scan = 5000

        while scanned < max_scan:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                response = await api.chat.chat_message.get(
                    ChatMessageGetRequest(
                        chat_id=chat_id,
                        limit=limit,
                        offset=offset,
                        include_staff_private=True,
                    )
                )
            if not response.ok:
                logger.warning(
                    "ChatMessage/Get rejected while recovering by external_message_id: ci=%s chat_id=%s payload=%s",
                    connected_integration_id,
                    chat_id,
                    response.result,
                )
                return None

            rows = response.result or []
            if not rows:
                return None

            for row in rows:
                if str(row.external_message_id or "").strip() == ext:
                    found = str(row.id or "").strip()
                    if found:
                        return found

            batch_len = len(rows)
            scanned += batch_len

            next_offset = response.next_offset
            if isinstance(next_offset, int) and next_offset > offset:
                offset = next_offset
            else:
                offset += batch_len

            if batch_len < limit:
                return None
            if response.total is not None and offset >= int(response.total):
                return None

        return None

    @classmethod
    async def _add_or_get_regos_message_by_telegram(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
        tg_message_id: int,
        lead_id: int,
        chat_id: str,
        text: Optional[str],
        file_ids: List[int],
    ) -> Optional[str]:
        ext_message_id = _tg_external_message_id(bot_hash, tg_chat_id, tg_message_id)
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            add_response = await api.call(
                "ChatMessage/Add",
                ChatMessageAddRequest(
                    chat_id=chat_id,
                    author_entity_type="Lead",
                    author_entity_id=lead_id,
                    message_type=ChatMessageTypeEnum.Regular,
                    text=text,
                    file_ids=file_ids or None,
                    external_message_id=ext_message_id,
                ),
                APIBaseResponse[Dict[str, Any]],
            )
        if not add_response.ok:
            result_payload = (
                add_response.result if isinstance(add_response.result, dict) else {}
            )
            error_code = result_payload.get("error")
            error_description = result_payload.get("description")
            error_code_int = _parse_int(str(error_code or ""), None)
            await cls._clear_cached_target_mapping(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_hash,
                tg_chat_id=tg_chat_id,
                lead_id=lead_id,
                chat_id=chat_id,
            )
            logger.warning(
                "Cleared cached mapping after ChatMessage/Add reject: ci=%s lead_id=%s chat_id=%s bot_hash=%s tg_chat_id=%s",
                connected_integration_id,
                lead_id,
                chat_id,
                bot_hash,
                tg_chat_id,
            )
            if (
                error_code_int
                == TelegramBotCrmChannelConfig.CHAT_MESSAGE_ADD_CLOSED_ENTITY_ERROR
            ):
                raise ChatMessageAddClosedEntityError(error_description)
            raise RuntimeError(
                "ChatMessage/Add rejected: "
                f"error={error_code} description={error_description}"
            )

        msg_uuid = ""
        if isinstance(add_response.result, dict):
            msg_uuid = str(add_response.result.get("new_uuid") or "").strip()
        else:
            msg_uuid = str(getattr(add_response.result, "new_uuid", "") or "").strip()
        if not msg_uuid:
            raise RuntimeError("ChatMessage/Add did not return new_uuid")

        await cls._redis_set_mapping(
            cls._msgmap_tg_to_regos_key(
                connected_integration_id, bot_hash, tg_chat_id, tg_message_id
            ),
            msg_uuid,
        )
        logger.debug(
            "ChatMessage/Add accepted: ci=%s lead_id=%s chat_id=%s msg_uuid=%s ext_id=%s",
            connected_integration_id,
            lead_id,
            chat_id,
            msg_uuid,
            ext_message_id,
        )
        return msg_uuid

    @classmethod
    async def _edit_regos_message_from_telegram(
        cls,
        connected_integration_id: str,
        regos_message_id: str,
        text: str,
        file_ids: List[int],
    ) -> None:
        payload: Dict[str, Any] = {
            "id": regos_message_id,
            "text": text,
            "file_ids": file_ids,
        }
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.call(
                "ChatMessage/Edit",
                payload,
                APIBaseResponse[Dict[str, Any]],
            )
        if response.ok:
            return

        result_payload = response.result if isinstance(response.result, dict) else {}
        raise RuntimeError(
            "ChatMessage/Edit rejected: "
            f"error={result_payload.get('error')} "
            f"description={result_payload.get('description')}"
        )

    @classmethod
    async def _delete_regos_message_from_telegram(
        cls,
        connected_integration_id: str,
        regos_message_id: str,
    ) -> None:
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.call(
                "ChatMessage/Delete",
                {"id": regos_message_id},
                APIBaseResponse[Dict[str, Any]],
            )
        if response.ok:
            return

        result_payload = response.result if isinstance(response.result, dict) else {}
        raise RuntimeError(
            "ChatMessage/Delete rejected: "
            f"error={result_payload.get('error')} "
            f"description={result_payload.get('description')}"
        )

    @classmethod
    async def _mark_chat_read_best_effort(
        cls,
        connected_integration_id: str,
        chat_id: str,
    ) -> None:
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                response = await api.chat.chat_message.mark_read(
                    ChatMessageMarkReadRequest(chat_id=chat_id)
                )
            if not response.ok:
                payload = response.result if isinstance(response.result, dict) else {}
                logger.warning(
                    "ChatMessage/MarkRead rejected: ci=%s chat_id=%s error=%s description=%s",
                    connected_integration_id,
                    chat_id,
                    payload.get("error"),
                    payload.get("description"),
                )
        except Exception as error:
            logger.warning(
                "ChatMessage/MarkRead failed: ci=%s chat_id=%s error=%s",
                connected_integration_id,
                chat_id,
                error,
            )

    @classmethod
    async def _set_lead_status_best_effort(
        cls,
        connected_integration_id: str,
        lead_id: Optional[int],
        status: LeadStatusEnum,
        *,
        reason: str,
    ) -> None:
        if not lead_id:
            logger.debug(
                "Skip Lead/SetStatus: ci=%s lead_id=%s to_status=%s reason=%s skip_reason=empty_lead_id",
                connected_integration_id,
                lead_id,
                status,
                reason,
            )
            return

        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                lead = await api.crm.lead.get_by_id(lead_id)
                if not lead:
                    logger.debug(
                        "Skip Lead/SetStatus: ci=%s lead_id=%s to_status=%s reason=%s skip_reason=lead_not_found",
                        connected_integration_id,
                        lead_id,
                        status,
                        reason,
                    )
                    return

                current_status: Optional[LeadStatusEnum]
                if isinstance(lead.status, LeadStatusEnum):
                    current_status = lead.status
                else:
                    try:
                        current_status = LeadStatusEnum(str(lead.status or "").strip())
                    except ValueError:
                        current_status = None
                if current_status in {LeadStatusEnum.Closed, LeadStatusEnum.Converted}:
                    logger.debug(
                        "Skip Lead/SetStatus: ci=%s lead_id=%s from_status=%s to_status=%s reason=%s skip_reason=terminal_status",
                        connected_integration_id,
                        lead_id,
                        current_status,
                        status,
                        reason,
                    )
                    return
                if (
                    current_status == LeadStatusEnum.New
                    and not getattr(lead, "responsible_user_id", None)
                ):
                    logger.debug(
                        "Skip Lead/SetStatus: ci=%s lead_id=%s from_status=%s to_status=%s reason=%s skip_reason=new_without_responsible",
                        connected_integration_id,
                        lead_id,
                        current_status,
                        status,
                        reason,
                    )
                    return
                if current_status == status:
                    logger.debug(
                        "Skip Lead/SetStatus: ci=%s lead_id=%s from_status=%s to_status=%s reason=%s skip_reason=already_target_status",
                        connected_integration_id,
                        lead_id,
                        current_status,
                        status,
                        reason,
                    )
                    return

                response = await api.crm.lead.set_status(
                    LeadSetStatusRequest(id=lead_id, status=status.value)
                )
            if response.ok:
                logger.debug(
                    "Lead/SetStatus applied: ci=%s lead_id=%s from_status=%s to_status=%s reason=%s",
                    connected_integration_id,
                    lead_id,
                    current_status,
                    status,
                    reason,
                )
                return

            payload = response.result if isinstance(response.result, dict) else {}
            logger.warning(
                "Lead/SetStatus rejected: ci=%s lead_id=%s from_status=%s to_status=%s reason=%s error=%s description=%s",
                connected_integration_id,
                lead_id,
                current_status,
                status,
                reason,
                payload.get("error"),
                payload.get("description"),
            )
        except Exception as error:
            logger.warning(
                "Lead status update failed: ci=%s lead_id=%s to_status=%s reason=%s error=%s",
                connected_integration_id,
                lead_id,
                status,
                reason,
                error,
            )

    @classmethod
    async def _set_lead_status_by_chat_best_effort(
        cls,
        connected_integration_id: str,
        chat_id: str,
        status: LeadStatusEnum,
        *,
        reason: str,
    ) -> None:
        lead_id = await cls._resolve_lead_id_by_chat(
            connected_integration_id=connected_integration_id,
            chat_id=chat_id,
        )
        if not lead_id:
            logger.debug(
                "Skip Lead/SetStatus by chat: ci=%s chat_id=%s to_status=%s reason=%s skip_reason=lead_not_resolved_by_chat",
                connected_integration_id,
                chat_id,
                status,
                reason,
            )
            return
        await cls._set_lead_status_best_effort(
            connected_integration_id=connected_integration_id,
            lead_id=lead_id,
            status=status,
            reason=reason,
        )

    @classmethod
    async def _clear_cached_target_mapping(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
        lead_id: Optional[int] = None,
        chat_id: Optional[str] = None,
    ) -> None:
        mapping_by_tg_key = cls._mapping_by_tg_key(
            connected_integration_id, bot_hash, tg_chat_id
        )
        cached_payload = cls._parse_cached_mapping(await cls._redis_get(mapping_by_tg_key))
        if cached_payload:
            if lead_id is None:
                lead_id = _parse_int(str(cached_payload.get("lead_id") or ""))
            if chat_id is None:
                chat_id = str(cached_payload.get("chat_id") or "").strip() or None

        await cls._redis_delete(
            mapping_by_tg_key,
            cls._lead_sync_cache_key(connected_integration_id, lead_id)
            if lead_id
            else "",
            cls._mapping_by_chat_key(connected_integration_id, str(chat_id))
            if chat_id
            else "",
        )

    @classmethod
    async def _resolve_cached_lead_mapping(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
    ) -> Tuple[Optional[int], Optional[str]]:
        # Redis-only fast path used before any CRM lookup/create.
        cached_payload = cls._parse_cached_mapping(
            await cls._redis_get(
                cls._mapping_by_tg_key(connected_integration_id, bot_hash, tg_chat_id)
            )
        )
        if not cached_payload:
            return None, None

        lead_id = _parse_int(str(cached_payload.get("lead_id") or ""))
        chat_id = str(cached_payload.get("chat_id") or "").strip()
        if not lead_id:
            return None, None
        if not chat_id:
            return None, None
        return lead_id, chat_id

    @classmethod
    async def _resolve_or_create_lead(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        bot_cfg: BotSlotConfig,
        tg_chat_id: str,
        message: Dict[str, Any],
    ) -> Tuple[Optional[int], Optional[str]]:
        cached_lead_id, cached_chat_id = await cls._resolve_cached_lead_mapping(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_cfg.bot_hash,
            tg_chat_id=tg_chat_id,
        )
        if cached_lead_id and cached_chat_id:
            return cached_lead_id, cached_chat_id

        recovered = await cls._recover_lead_by_external_chat(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_cfg.bot_hash,
            tg_chat_id=tg_chat_id,
        )
        if recovered:
            await cls._save_lead_mapping(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_cfg.bot_hash,
                tg_chat_id=tg_chat_id,
                lead=recovered,
            )
            return recovered.id, recovered.chat_id

        lock_key = cls._lock_create_lead_key(connected_integration_id, bot_cfg.bot_hash, tg_chat_id)
        lock_token = await cls._acquire_lock(lock_key, runtime.state_ttl_sec)
        if not lock_token:
            await asyncio.sleep(0.25)
            # Another worker may have created the lead while we were waiting.
            cached_lead_id, cached_chat_id = await cls._resolve_cached_lead_mapping(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_cfg.bot_hash,
                tg_chat_id=tg_chat_id,
            )
            if cached_lead_id and cached_chat_id:
                return cached_lead_id, cached_chat_id
            return None, None

        try:
            # Double-check mapping under lock to avoid duplicate lead creation.
            cached_lead_id, cached_chat_id = await cls._resolve_cached_lead_mapping(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_cfg.bot_hash,
                tg_chat_id=tg_chat_id,
            )
            if cached_lead_id and cached_chat_id:
                return cached_lead_id, cached_chat_id

            lead_subject = cls._build_subject(
                bot_cfg.lead_subject_template, message, tg_chat_id
            )
            contact_payload = cls._extract_contact_payload(message, tg_chat_id)
            client_name = contact_payload["display_name"] or None

            client_phone = cls._normalize_text_value(cls._extract_own_contact_phone(message))
            client_photo_url = await cls._resolve_client_photo_url(bot_cfg, message)
            logger.debug(
                "Lead create payload prepared: ci=%s bot_hash=%s tg_chat_id=%s has_avatar=%s has_phone=%s",
                connected_integration_id,
                bot_cfg.bot_hash,
                tg_chat_id,
                bool(client_photo_url),
                bool(client_phone),
            )

            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                add_resp = await api.crm.lead.add(
                    LeadAddRequest(
                        channel_id=bot_cfg.channel_id,
                        pipeline_id=bot_cfg.pipeline_id,
                        responsible_user_id=bot_cfg.default_responsible_user_id,
                        subject=lead_subject,
                        external_id=_lead_external_id(bot_cfg.bot_hash, tg_chat_id),
                        client_name=client_name,
                        client_phone=client_phone,
                        client_photo_url=client_photo_url,
                    )
                )
                new_id = None
                if add_resp.result:
                    new_id = _parse_int(str(add_resp.result.new_id))
                if not new_id:
                    raise RuntimeError("Lead/Add did not return new_id")

                lead = await api.crm.lead.get_by_id(new_id)
                if not lead or not lead.chat_id:
                    raise RuntimeError("Lead/Get did not return chat_id")
                logger.debug(
                    "Lead created/reused by Lead/Add: ci=%s bot_hash=%s tg_chat_id=%s lead_id=%s lead_has_avatar=%s",
                    connected_integration_id,
                    bot_cfg.bot_hash,
                    tg_chat_id,
                    lead.id,
                    bool(cls._normalize_text_value(getattr(lead, "client_photo_url", None))),
                )

            await cls._save_lead_mapping(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_cfg.bot_hash,
                tg_chat_id=tg_chat_id,
                lead=lead,
            )
            return lead.id, lead.chat_id
        finally:
            await cls._release_lock(lock_key, lock_token)

    @classmethod
    async def _resolve_existing_lead(
        cls,
        connected_integration_id: str,
        bot_cfg: BotSlotConfig,
        tg_chat_id: str,
    ) -> Tuple[Optional[int], Optional[str]]:
        cached_lead_id, cached_chat_id = await cls._resolve_cached_lead_mapping(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_cfg.bot_hash,
            tg_chat_id=tg_chat_id,
        )
        if cached_lead_id and cached_chat_id:
            return cached_lead_id, cached_chat_id

        recovered = await cls._recover_lead_by_external_chat(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_cfg.bot_hash,
            tg_chat_id=tg_chat_id,
        )
        if not recovered:
            return None, None

        await cls._save_lead_mapping(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_cfg.bot_hash,
            tg_chat_id=tg_chat_id,
            lead=recovered,
        )
        return recovered.id, recovered.chat_id

    @classmethod
    async def _recover_lead_by_external_chat(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
    ) -> Optional[Lead]:
        filters = [
            Filter(
                field="external_id",
                operator=FilterOperator.Equal,
                value=_lead_external_id(bot_hash, tg_chat_id),
            ),
        ]
        statuses = [
            LeadStatusEnum.New,
            LeadStatusEnum.InProgress,
            LeadStatusEnum.WaitingClient,
        ]
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.crm.lead.get(
                LeadGetRequest(
                    filters=filters,
                    statuses=statuses,
                    limit=1,
                    offset=0,
                )
            )
        if not response.result:
            return None
        lead = response.result[0]
        if not lead or not lead.id or not lead.chat_id:
            return None
        return lead

    @classmethod
    async def _save_lead_mapping(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
        lead: Lead,
    ) -> None:
        if not (lead.id and lead.chat_id):
            return
        await cls._save_cached_mapping(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_hash,
            tg_chat_id=tg_chat_id,
            lead_id=int(lead.id),
            chat_id=str(lead.chat_id),
        )

    @classmethod
    async def _upload_telegram_files(
        cls,
        connected_integration_id: str,
        bot_cfg: BotSlotConfig,
        chat_id: str,
        message: Dict[str, Any],
    ) -> Tuple[List[int], int]:
        files = cls._extract_files_from_message(message)
        if not files:
            return [], 0

        uploaded_ids: List[int] = []
        oversized_files_count = 0
        max_size_bytes = TelegramBotCrmChannelConfig.MAX_TELEGRAM_FILE_SIZE_BYTES
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            for file_meta in files:
                file_id_raw = str(file_meta.get("file_id") or "").strip()
                file_name = str(file_meta.get("name") or "file.bin")
                reported_size = _parse_int(
                    str(file_meta.get("size_bytes") or ""),
                    default=None,
                )
                if reported_size and reported_size > max_size_bytes:
                    oversized_files_count += 1
                    logger.info(
                        "Skip telegram file above size limit: ci=%s chat_id=%s file=%s size=%sB limit=%sB",
                        connected_integration_id,
                        chat_id,
                        file_name,
                        reported_size,
                        max_size_bytes,
                    )
                    continue
                try:
                    file_bytes = await cls._download_telegram_file(
                        token=bot_cfg.token,
                        file_id=file_id_raw,
                        max_size_bytes=max_size_bytes,
                    )
                except TelegramFileTooLargeError as exc:
                    oversized_files_count += 1
                    logger.info(
                        "Skip telegram file above size limit (from get_file): ci=%s chat_id=%s file=%s size=%sB limit=%sB",
                        connected_integration_id,
                        chat_id,
                        file_name,
                        exc.size_bytes,
                        exc.limit_bytes,
                    )
                    continue
                payload_b64 = base64.b64encode(file_bytes).decode("ascii")
                response = await api.call(
                    "ChatMessage/AddFile",
                    ChatMessageAddFileRequest(
                        chat_id=chat_id,
                        name=file_meta["name"],
                        extension=file_meta["extension"],
                        data=payload_b64,
                    ),
                    APIBaseResponse[Dict[str, Any]],
                )
                result_payload = response.result if isinstance(response.result, dict) else {}
                if not response.ok:
                    error_code = result_payload.get("error")
                    error_description = result_payload.get("description")
                    raise RuntimeError(
                        "ChatMessage/AddFile rejected: "
                        f"error={error_code} description={error_description}"
                    )
                file_id = _parse_int(str(result_payload.get("file_id") or ""))
                if not file_id:
                    raise RuntimeError("ChatMessage/AddFile did not return file_id")
                uploaded_ids.append(file_id)
        return uploaded_ids, oversized_files_count

    @staticmethod
    def _extract_files_from_message(message: Dict[str, Any]) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        message_id = str(message.get("message_id") or _now_ts())

        document = message.get("document")
        if isinstance(document, dict) and document.get("file_id"):
            file_name = _sanitize_file_name(str(document.get("file_name") or "document.bin"))
            result.append(
                {
                    "file_id": str(document["file_id"]),
                    "name": file_name,
                    "extension": _file_ext_from_name(file_name, "bin"),
                    "size_bytes": _parse_int(str(document.get("file_size") or ""), None),
                }
                )

        photos = message.get("photo")
        if isinstance(photos, list) and photos:
            best_photo = max(
                [row for row in photos if isinstance(row, dict) and row.get("file_id")],
                key=lambda row: int(row.get("file_size") or 0),
                default=None,
            )
            if best_photo:
                result.append(
                    {
                        "file_id": str(best_photo["file_id"]),
                        "name": f"photo_{message_id}.jpg",
                        "extension": "jpg",
                        "size_bytes": _parse_int(str(best_photo.get("file_size") or ""), None),
                    }
                )

        video = message.get("video")
        if isinstance(video, dict) and video.get("file_id"):
            video_name_raw = str(video.get("file_name") or "").strip()
            if video_name_raw:
                video_name = _sanitize_file_name(video_name_raw)
                video_ext = _file_ext_from_name(video_name, "mp4")
            else:
                video_ext = _file_ext_from_mime(video.get("mime_type"), "mp4")
                video_name = f"video_{message_id}.{video_ext}"
            result.append(
                {
                    "file_id": str(video["file_id"]),
                    "name": video_name,
                    "extension": video_ext,
                    "size_bytes": _parse_int(str(video.get("file_size") or ""), None),
                }
            )

        video_note = message.get("video_note")
        if isinstance(video_note, dict) and video_note.get("file_id"):
            video_note_ext = _file_ext_from_mime(video_note.get("mime_type"), "mp4")
            result.append(
                {
                    "file_id": str(video_note["file_id"]),
                    "name": f"video_note_{message_id}.{video_note_ext}",
                    "extension": video_note_ext,
                    "size_bytes": _parse_int(str(video_note.get("file_size") or ""), None),
                }
            )

        audio = message.get("audio")
        if isinstance(audio, dict) and audio.get("file_id"):
            audio_name_raw = str(audio.get("file_name") or "").strip()
            if audio_name_raw:
                audio_name = _sanitize_file_name(audio_name_raw)
                audio_ext = _file_ext_from_name(audio_name, "mp3")
            else:
                audio_ext = _file_ext_from_mime(audio.get("mime_type"), "mp3")
                audio_name = f"audio_{message_id}.{audio_ext}"
            result.append(
                {
                    "file_id": str(audio["file_id"]),
                    "name": audio_name,
                    "extension": audio_ext,
                    "size_bytes": _parse_int(str(audio.get("file_size") or ""), None),
                }
            )

        voice = message.get("voice")
        if isinstance(voice, dict) and voice.get("file_id"):
            voice_ext = _file_ext_from_mime(voice.get("mime_type"), "ogg")
            voice_name = f"voice_{message_id}.{voice_ext}"
            result.append(
                {
                    "file_id": str(voice["file_id"]),
                    "name": voice_name,
                    "extension": voice_ext,
                    "size_bytes": _parse_int(str(voice.get("file_size") or ""), None),
                }
            )
        return result

    @classmethod
    async def _download_telegram_file(
        cls,
        token: str,
        file_id: str,
        max_size_bytes: Optional[int] = None,
    ) -> bytes:
        bot = await cls._get_bot(token)
        file_info = await bot.get_file(file_id)
        if max_size_bytes and max_size_bytes > 0:
            resolved_size = _parse_int(str(getattr(file_info, "file_size", "") or ""), None)
            if resolved_size and resolved_size > max_size_bytes:
                raise TelegramFileTooLargeError(
                    size_bytes=resolved_size, limit_bytes=max_size_bytes
                )
        file_path = str(file_info.file_path or "").strip()
        if not file_path:
            raise RuntimeError("Telegram file_path is empty")
        url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        client = await cls._get_http_client()
        response = await client.get(url)
        response.raise_for_status()
        return response.content

    @classmethod
    async def _process_regos_event(
        cls, connected_integration_id: str, fields: Dict[str, str]
    ) -> None:
        runtime = await cls._load_runtime(connected_integration_id)
        action = str(fields.get("action") or "").strip()
        payload_raw = fields.get("payload")
        payload = _json_loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        if not isinstance(payload, dict):
            payload = {}

        event_id_raw = str(fields.get("event_id") or "").strip()
        if not event_id_raw:
            stable = f"{action}:{_json_dumps(payload)}"
            event_id_raw = hashlib.md5(stable.encode("utf-8")).hexdigest()
        dedupe_key = cls._dedupe_webhook_key(connected_integration_id, event_id_raw)
        if await cls._redis_get(dedupe_key):
            return
        dedupe_lock_key = f"{dedupe_key}:lock"
        dedupe_lock_token = await cls._acquire_lock(dedupe_lock_key, 120)
        if not dedupe_lock_token:
            logger.debug(
                "Skip duplicate REGOS event (in-flight): ci=%s action=%s event_id=%s",
                connected_integration_id,
                action,
                event_id_raw,
            )
            return

        try:
            if await cls._redis_get(dedupe_key):
                return

            handlers = {
                "ChatMessageAdded": cls._handle_chat_message_added,
                "ChatMessageEdited": cls._handle_chat_message_edited,
                "ChatMessageDeleted": cls._handle_chat_message_deleted,
                "ChatWriting": cls._handle_chat_writing,
                "LeadClosed": cls._handle_lead_closed,
            }
            handler = handlers.get(action)
            if handler:
                await handler(connected_integration_id, runtime, payload)

            await cls._redis_set_with_ttl(dedupe_key, "1", runtime.lead_dedupe_ttl_sec)
        finally:
            await cls._release_lock(dedupe_lock_key, dedupe_lock_token)

    @classmethod
    def _build_delivery_alert_external_message_id(
        cls,
        action: str,
        payload: Dict[str, Any],
        event_id: Optional[str],
    ) -> str:
        normalized_event_id = str(event_id or "").strip()
        if not normalized_event_id:
            stable = f"{action}:{_json_dumps(payload)}"
            normalized_event_id = hashlib.md5(stable.encode("utf-8")).hexdigest()
        prefix = TelegramBotCrmChannelConfig.ALERT_EXTERNAL_PREFIX
        return f"{prefix}:{action}:{normalized_event_id}"[:150]

    @staticmethod
    def _delivery_action_label(action: str) -> str:
        labels = {
            "ChatMessageAdded": "отправка сообщения",
            "ChatMessageEdited": "редактирование сообщения",
            "ChatMessageDeleted": "удаление сообщения",
            "LeadClosed": "уведомление о закрытии лида",
        }
        return labels.get(str(action or "").strip(), str(action or "").strip() or "неизвестно")

    @staticmethod
    def _short_error_text(error_text: str) -> str:
        short_error = re.sub(r"\s+", " ", str(error_text or "").strip())
        if len(short_error) > 500:
            short_error = short_error[:500] + "..."
        return short_error

    @classmethod
    def _humanize_delivery_error_reason(cls, error_text: str) -> str:
        raw = cls._short_error_text(error_text)
        lower = raw.lower()
        if not lower:
            return "Неизвестная ошибка доставки."

        if "bot was blocked by the user" in lower:
            return "Пользователь заблокировал бота."
        if "bot can't initiate conversation with a user" in lower:
            return "Бот не может начать диалог первым. Пользователь должен написать боту."
        if "chat not found" in lower or "user not found" in lower:
            return "Чат не найден. Пользователь мог удалить чат или не запускал бота."
        if "forbidden" in lower:
            return "Telegram запретил отправку в этот чат."
        if "message is not modified" in lower:
            return "Текст не изменился, Telegram отклонил повторное редактирование."
        if "message to edit not found" in lower:
            return "Сообщение для редактирования не найдено в Telegram."
        if "message can't be edited" in lower:
            return "Это сообщение нельзя редактировать в Telegram."
        if "message to delete not found" in lower:
            return "Сообщение для удаления не найдено в Telegram."
        if "message can't be deleted" in lower:
            return "Это сообщение нельзя удалить в Telegram."
        if "can't parse entities" in lower:
            return "Некорректная разметка сообщения для Telegram."
        if "too many requests" in lower or "retry after" in lower or "flood control" in lower:
            return "Telegram временно ограничил частоту запросов."
        if "timed out" in lower or "timeout" in lower:
            return "Таймаут при обращении к Telegram."
        if (
            "name or service not known" in lower
            or "temporary failure in name resolution" in lower
            or "nodename nor servname provided" in lower
        ):
            return "DNS-ошибка при обращении к Telegram."
        if (
            "connection reset" in lower
            or "connection refused" in lower
            or "network is unreachable" in lower
            or "server disconnected" in lower
        ):
            return "Сетевая ошибка при обращении к Telegram."
        if "telegram file exceeds size limit" in lower:
            return "Файл превышает допустимый размер для Telegram."

        return "Ошибка доставки в Telegram."

    @staticmethod
    def _format_delivery_alert_text(
        action: str,
        payload: Dict[str, Any],
        error_text: str,
    ) -> str:
        source_message_id = str(payload.get("id") or "").strip() or "-"
        source_chat_id = str(payload.get("chat_id") or "").strip() or "-"
        action_label = TelegramBotCrmChannelIntegration._delivery_action_label(action)
        human_reason = TelegramBotCrmChannelIntegration._humanize_delivery_error_reason(error_text)
        technical_reason = TelegramBotCrmChannelIntegration._short_error_text(error_text)
        include_technical_reason = bool(
            technical_reason and technical_reason.lower() != human_reason.lower()
        )
        technical_reason_line = (
            f"\nТехническая причина: {technical_reason}" if include_technical_reason else ""
        )
        return (
            "[Telegram Integration] Не удалось выполнить событие в Telegram.\n"
            f"Операция: {action_label}\n"
            f"Chat: {source_chat_id}\n"
            f"Message: {source_message_id}\n"
            f"Причина: {human_reason}"
            f"{technical_reason_line}"
        )

    @classmethod
    async def _resolve_alert_chat_id(
        cls,
        connected_integration_id: str,
        action: str,
        payload: Dict[str, Any],
    ) -> Optional[str]:
        chat_id = str(payload.get("chat_id") or "").strip()
        if chat_id:
            return chat_id
        if action != "LeadClosed":
            return None

        lead_id = _parse_int(str(payload.get("id") or ""))
        if not lead_id:
            return None

        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                lead = await api.crm.lead.get_by_id(lead_id)
            return str(getattr(lead, "chat_id", "") or "").strip() or None
        except Exception:
            return None

    @classmethod
    async def _notify_telegram_delivery_issue_best_effort(
        cls,
        connected_integration_id: str,
        fields: Dict[str, str],
        error_text: str,
    ) -> None:
        action = str(fields.get("action") or "").strip()
        if action not in {"ChatMessageAdded", "ChatMessageEdited", "ChatMessageDeleted", "LeadClosed"}:
            return

        payload_raw = fields.get("payload")
        payload = _json_loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        payload = payload if isinstance(payload, dict) else {}

        chat_id = await cls._resolve_alert_chat_id(
            connected_integration_id=connected_integration_id,
            action=action,
            payload=payload,
        )
        if not chat_id:
            return

        alert_text = cls._format_delivery_alert_text(action, payload, error_text)
        alert_external_id = cls._build_delivery_alert_external_message_id(
            action=action,
            payload=payload,
            event_id=str(fields.get("event_id") or "").strip() or None,
        )

        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                add_resp = await api.call(
                    "ChatMessage/Add",
                    ChatMessageAddRequest(
                        chat_id=chat_id,
                        message_type=ChatMessageTypeEnum.System,
                        text=alert_text,
                        external_message_id=alert_external_id,
                    ),
                    APIBaseResponse[Dict[str, Any]],
                )
                if add_resp.ok:
                    return
                logger.warning(
                    "Delivery alert system message rejected: ci=%s action=%s chat_id=%s payload=%s",
                    connected_integration_id,
                    action,
                    chat_id,
                    add_resp.result,
                )
        except Exception as notify_error:
            logger.warning(
                "Failed to post Telegram delivery alert: ci=%s action=%s chat_id=%s error=%s",
                connected_integration_id,
                action,
                chat_id,
                notify_error,
            )

    @classmethod
    async def _resolve_lead_id_by_chat(
        cls,
        connected_integration_id: str,
        chat_id: str,
    ) -> Optional[int]:
        active_statuses = [
            LeadStatusEnum.New,
            LeadStatusEnum.InProgress,
            LeadStatusEnum.WaitingClient,
        ]
        mapping_by_chat_key = cls._mapping_by_chat_key(connected_integration_id, chat_id)
        cached_payload = cls._parse_cached_mapping(await cls._redis_get(mapping_by_chat_key)) or {}
        cached_lead_id = _parse_int(str(cached_payload.get("lead_id") or ""))
        if cached_lead_id:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                cached_lead = await api.crm.lead.get_by_id(cached_lead_id)
            if cached_lead and cached_lead.status in active_statuses:
                return cached_lead_id
            logger.debug(
                "Cached lead by chat is not active: ci=%s chat_id=%s cached_lead_id=%s cached_status=%s",
                connected_integration_id,
                chat_id,
                cached_lead_id,
                cached_lead.status if cached_lead else None,
            )

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            chat_response = await api.call(
                "Chat/Get",
                {"ids": [chat_id], "limit": 1, "offset": 0},
                APIBaseResponse[List[Dict[str, Any]]],
            )
            if not chat_response.ok:
                logger.warning(
                    "Chat/Get rejected while resolving lead by chat: ci=%s chat_id=%s payload=%s",
                    connected_integration_id,
                    chat_id,
                    chat_response.result,
                )
                return None

            chat_rows = chat_response.result or []
            if not chat_rows:
                return None
            lead_ids = cls._extract_lead_ids_from_chat_payload(chat_rows[0])
            if not lead_ids:
                return None
            lead_response = await api.crm.lead.get(
                LeadGetRequest(
                    ids=lead_ids,
                    statuses=active_statuses,
                    limit=len(lead_ids),
                    offset=0,
                )
            )
        if not lead_response.ok:
            logger.warning(
                "Lead/Get rejected while resolving active lead by chat: ci=%s chat_id=%s lead_ids=%s payload=%s",
                connected_integration_id,
                chat_id,
                lead_ids,
                lead_response.result,
            )
            return None
        active_rows = lead_response.result or []
        if not isinstance(active_rows, list):
            return None
        if not active_rows:
            logger.debug(
                "No active lead in chat participants: ci=%s chat_id=%s lead_ids=%s",
                connected_integration_id,
                chat_id,
                lead_ids,
            )
            return None

        # In repeated-lead flow old closed lead may remain in participants.
        # We always target the latest active lead for status updates.
        lead_id = max(
            (
                int(lead.id)
                for lead in active_rows
                if lead and lead.id and int(lead.id) > 0
            ),
            default=0,
        )
        if not lead_id:
            return None

        bot_hash = str(cached_payload.get("bot_hash") or "").strip()
        tg_chat_id = str(cached_payload.get("tg_chat_id") or "").strip()
        if bot_hash and tg_chat_id:
            await cls._save_cached_mapping(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_hash,
                tg_chat_id=tg_chat_id,
                lead_id=lead_id,
                chat_id=chat_id,
            )
        else:
            await cls._redis_set_mapping(
                mapping_by_chat_key,
                _json_dumps({"lead_id": int(lead_id), "chat_id": chat_id}),
            )
        return lead_id

    @classmethod
    async def _resolve_target_by_chat(
        cls, connected_integration_id: str, chat_id: str
    ) -> Optional[Tuple[str, str]]:
        cached_payload = cls._parse_cached_mapping(
            await cls._redis_get(cls._mapping_by_chat_key(connected_integration_id, chat_id))
        )
        if cached_payload:
            bot_hash = str(cached_payload.get("bot_hash") or "").strip()
            tg_chat_id = str(cached_payload.get("tg_chat_id") or "").strip()
            if bot_hash and tg_chat_id:
                return bot_hash, tg_chat_id

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            chat_response = await api.call(
                "Chat/Get",
                {"ids": [chat_id], "limit": 1, "offset": 0},
                APIBaseResponse[List[Dict[str, Any]]],
            )
            if not chat_response.ok:
                logger.warning(
                    "Chat/Get rejected while resolving target: ci=%s chat_id=%s payload=%s",
                    connected_integration_id,
                    chat_id,
                    chat_response.result,
                )
                return None

            chat_rows = chat_response.result or []
            if not chat_rows:
                return None

            lead_id = cls._extract_lead_id_from_chat_payload(chat_rows[0])
            if not lead_id:
                return None

            lead_response = await api.call(
                "Lead/Get",
                LeadGetRequest(ids=[lead_id], limit=1, offset=0),
                APIBaseResponse[List[Dict[str, Any]]],
            )
            if not lead_response.ok:
                logger.warning(
                    "Lead/Get rejected while resolving target: ci=%s chat_id=%s lead_id=%s payload=%s",
                    connected_integration_id,
                    chat_id,
                    lead_id,
                    lead_response.result,
                )
                return None

        lead_rows = lead_response.result or []
        if not lead_rows:
            return None
        lead = Lead.model_validate(lead_rows[0])
        if not (lead and lead.id):
            return None
        bot_hash, tg_chat_id = _parse_tg_lead_external_id(getattr(lead, "external_id", None))
        if not bot_hash or not tg_chat_id:
            return None
        await cls._save_cached_mapping(
            connected_integration_id=connected_integration_id,
            bot_hash=str(bot_hash),
            tg_chat_id=str(tg_chat_id),
            lead_id=int(lead.id),
            chat_id=chat_id,
        )
        return str(bot_hash), str(tg_chat_id)

    @staticmethod
    def _extract_lead_id_from_chat_payload(chat_payload: Any) -> Optional[int]:
        lead_ids = TelegramBotCrmChannelIntegration._extract_lead_ids_from_chat_payload(
            chat_payload
        )
        if not lead_ids:
            return None
        return lead_ids[0]

    @staticmethod
    def _extract_lead_ids_from_chat_payload(chat_payload: Any) -> List[int]:
        if not isinstance(chat_payload, dict):
            return []
        participants = chat_payload.get("participants")
        if not isinstance(participants, list):
            return []
        lead_ids: List[int] = []
        seen_ids = set()
        for participant in participants:
            if not isinstance(participant, dict):
                continue
            entity_type_raw = str(participant.get("entity_type") or "").strip().lower()
            if not _is_lead_entity_type(entity_type_raw):
                continue
            entity_id = _parse_int(str(participant.get("entity_id") or ""))
            if not entity_id or entity_id <= 0:
                continue
            if entity_id in seen_ids:
                continue
            seen_ids.add(entity_id)
            lead_ids.append(int(entity_id))
        return lead_ids

    @classmethod
    async def _handle_chat_message_added(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        chat_id = str(payload.get("chat_id") or "").strip()
        message_id = str(payload.get("id") or "").strip()
        if not chat_id or not message_id:
            return

        telegram_target = await cls._resolve_target_by_chat(connected_integration_id, chat_id)
        if not telegram_target:
            return
        bot_hash, tg_chat_id = telegram_target
        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            chat_message_response = await api.chat.chat_message.get(
                ChatMessageGetRequest(
                    chat_id=chat_id,
                    ids=[message_id],
                    limit=1,
                    offset=0,
                    include_staff_private=True,
                )
            )
            if not chat_message_response.result:
                return
            chat_message = chat_message_response.result[0]
            if not chat_message:
                return
            if _is_telegram_internal_external_message(chat_message.external_message_id):
                return
            if (
                chat_message.message_type == ChatMessageTypeEnum.Private
                and not runtime.send_private_messages
            ):
                return
            if (
                chat_message.message_type == ChatMessageTypeEnum.System
                and not runtime.forward_system_messages
            ):
                return

            # CRM staff replied to the client -> lead is waiting for the client answer.
            is_regular_message = chat_message.message_type == ChatMessageTypeEnum.Regular
            is_operator_reply = _is_user_entity_type(chat_message.author_entity_type)
            if is_regular_message and is_operator_reply:
                await cls._set_lead_status_by_chat_best_effort(
                    connected_integration_id=connected_integration_id,
                    chat_id=chat_id,
                    status=LeadStatusEnum.WaitingClient,
                    reason="operator_reply",
                )
            else:
                logger.debug(
                    "Skip WaitingClient status on outbound relay: ci=%s chat_id=%s message_id=%s message_type=%s author_entity_type=%s",
                    connected_integration_id,
                    chat_id,
                    message_id,
                    chat_message.message_type,
                    chat_message.author_entity_type,
                )

            sent_tg_message_id = await cls._send_chat_message_to_telegram(
                bot_cfg=bot_cfg,
                tg_chat_id=tg_chat_id,
                text=chat_message.text or "",
                file_ids=chat_message.file_ids or [],
                connected_integration_id=connected_integration_id,
            )
            if not sent_tg_message_id:
                return

            await cls._redis_set_mapping(
                cls._msgmap_regos_to_tg_key(connected_integration_id, message_id),
                str(sent_tg_message_id),
            )

    @classmethod
    async def _send_chat_message_to_telegram(
        cls,
        bot_cfg: BotSlotConfig,
        tg_chat_id: str,
        text: str,
        file_ids: List[int],
        connected_integration_id: str,
    ) -> Optional[int]:
        bot = await cls._get_bot(bot_cfg.token)
        target_chat = _tg_chat_id_cast(tg_chat_id)
        first_sent_id: Optional[int] = None
        caption_used = False
        rendered_text, parse_mode = cls._crm_markdown_to_telegram_payload(text)

        files_map: Dict[int, Any] = {}
        if file_ids:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                files_resp = await api.files.file.get(
                    FileGetRequest(ids=file_ids, limit=len(file_ids), offset=0)
                )
            files_map = {int(item.id): item for item in (files_resp.result or []) if item and item.id}

        for file_id in file_ids:
            file_model = files_map.get(int(file_id))
            if not file_model or not file_model.url:
                continue
            file_bytes = await cls._download_regos_file_bytes(str(file_model.url))
            file_name_raw = str(file_model.name or "").strip()
            file_ext = str(file_model.extension or "").strip().lower()
            if not file_name_raw:
                file_name_raw = f"file_{file_id}.{file_ext or 'bin'}"
            elif "." not in file_name_raw and file_ext:
                file_name_raw = f"{file_name_raw}.{file_ext}"
            file_name = _sanitize_file_name(file_name_raw)
            input_file = BufferedInputFile(file_bytes, filename=file_name)
            caption = None
            if rendered_text and not caption_used:
                caption = rendered_text
                caption_used = True

            if _is_photo_extension(file_model.extension):
                sent = await bot.send_photo(
                    chat_id=target_chat,
                    photo=input_file,
                    caption=caption,
                    parse_mode=parse_mode if caption and parse_mode else None,
                )
            elif _is_video_extension(file_model.extension):
                sent = await bot.send_video(
                    chat_id=target_chat,
                    video=input_file,
                    caption=caption,
                    parse_mode=parse_mode if caption and parse_mode else None,
                )
            elif _is_voice_extension(file_model.extension):
                sent = await bot.send_voice(
                    chat_id=target_chat,
                    voice=input_file,
                    caption=caption,
                    parse_mode=parse_mode if caption and parse_mode else None,
                )
            elif _is_audio_extension(file_model.extension):
                sent = await bot.send_audio(
                    chat_id=target_chat,
                    audio=input_file,
                    caption=caption,
                    parse_mode=parse_mode if caption and parse_mode else None,
                )
            else:
                sent = await bot.send_document(
                    chat_id=target_chat,
                    document=input_file,
                    caption=caption,
                    parse_mode=parse_mode if caption and parse_mode else None,
                )
            if not first_sent_id:
                first_sent_id = int(sent.message_id)

        if rendered_text and not caption_used:
            sent = await bot.send_message(
                chat_id=target_chat,
                text=rendered_text,
                parse_mode=parse_mode,
            )
            if not first_sent_id:
                first_sent_id = int(sent.message_id)

        return first_sent_id

    @classmethod
    async def _download_regos_file_bytes(cls, url: str) -> bytes:
        source_url = str(url or "").strip()
        if not source_url:
            raise RuntimeError("REGOS file url is empty")
        client = await cls._get_http_client()
        response = await client.get(source_url)
        response.raise_for_status()
        return response.content

    @classmethod
    async def _handle_chat_message_edited(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        chat_id = str(payload.get("chat_id") or "").strip()
        message_id = str(payload.get("id") or "").strip()
        if not chat_id or not message_id:
            return

        target = await cls._resolve_target_by_chat(connected_integration_id, chat_id)
        if not target:
            return
        bot_hash, tg_chat_id = target
        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return

        mapped_id_raw = await cls._redis_get(
            cls._msgmap_regos_to_tg_key(connected_integration_id, message_id)
        )
        mapped_id = _parse_int(mapped_id_raw)

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.chat.chat_message.get(
                ChatMessageGetRequest(
                    chat_id=chat_id,
                    ids=[message_id],
                    limit=1,
                    offset=0,
                    include_staff_private=True,
                )
            )
            if not response.result:
                return
            msg = response.result[0]
            if not msg:
                return
            if _is_telegram_internal_external_message(msg.external_message_id):
                return

        bot = await cls._get_bot(bot_cfg.token)
        target_chat = _tg_chat_id_cast(tg_chat_id)
        text = (msg.text or "").strip()
        rendered_text, parse_mode = cls._crm_markdown_to_telegram_payload(text)

        if mapped_id and text:
            try:
                await bot.edit_message_text(
                    chat_id=target_chat,
                    message_id=int(mapped_id),
                    text=rendered_text,
                    parse_mode=parse_mode,
                )
                return
            except Exception:
                pass

        edited_text = f"(edited)\n{text}".strip()
        sent_id = await cls._send_chat_message_to_telegram(
            bot_cfg=bot_cfg,
            tg_chat_id=tg_chat_id,
            text=edited_text,
            file_ids=msg.file_ids or [],
            connected_integration_id=connected_integration_id,
        )
        if sent_id:
            await cls._redis_set_mapping(
                cls._msgmap_regos_to_tg_key(connected_integration_id, message_id),
                str(sent_id),
            )

    @classmethod
    async def _handle_chat_message_deleted(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        chat_id = str(payload.get("chat_id") or "").strip()
        message_id = str(payload.get("id") or "").strip()
        if not chat_id or not message_id:
            return
        target = await cls._resolve_target_by_chat(connected_integration_id, chat_id)
        if not target:
            return
        bot_hash, tg_chat_id = target
        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return
        mapped_id_raw = await cls._redis_get(
            cls._msgmap_regos_to_tg_key(connected_integration_id, message_id)
        )
        mapped_id = _parse_int(mapped_id_raw)
        if not mapped_id:
            return
        bot = await cls._get_bot(bot_cfg.token)
        try:
            await bot.delete_message(
                chat_id=_tg_chat_id_cast(tg_chat_id), message_id=int(mapped_id)
            )
        except Exception:
            pass

    @classmethod
    async def _handle_chat_writing(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        chat_id = str(payload.get("chat_id") or "").strip()
        if not chat_id:
            return

        author_entity_type = str(payload.get("author_entity_type") or "").strip().lower()
        author_entity_id = _parse_int(str(payload.get("author_entity_id") or ""))
        if _is_lead_entity_type(author_entity_type):
            logger.debug(
                "Skip ChatWriting relay for lead author: ci=%s chat_id=%s author_entity_id=%s",
                connected_integration_id,
                chat_id,
                author_entity_id,
            )
            return

        target = await cls._resolve_target_by_chat(connected_integration_id, chat_id)
        if not target:
            return
        bot_hash, tg_chat_id = target
        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return

        throttle_key = cls._typing_key(connected_integration_id, bot_hash, tg_chat_id)
        if author_entity_type or author_entity_id:
            throttle_key = (
                f"{throttle_key}:{author_entity_type or 'unknown'}:{author_entity_id or 0}"
            )
        can_send = await cls._redis_set_nx_with_ttl(throttle_key, "1", 3)
        if not can_send:
            return

        bot = await cls._get_bot(bot_cfg.token)
        try:
            await bot.send_chat_action(
                chat_id=_tg_chat_id_cast(tg_chat_id), action="typing"
            )
        except Exception:
            pass

    @classmethod
    async def _handle_lead_closed(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        lead_id = _parse_int(str(payload.get("id") or ""))
        if not lead_id:
            return
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            lead = await api.crm.lead.get_by_id(lead_id)
        if not lead:
            return

        text = runtime.lead_closed_message_template or "Обращение закрыто. Спасибо за обращение."
        if not text.strip():
            return

        bot_hash, tg_chat_id = _parse_tg_lead_external_id(getattr(lead, "external_id", None))
        bot_hash = str(bot_hash or "").strip()
        tg_chat_id = str(tg_chat_id or "").strip()
        if not bot_hash or not tg_chat_id:
            if lead.chat_id:
                target = await cls._resolve_target_by_chat(connected_integration_id, str(lead.chat_id))
                if target:
                    bot_hash, tg_chat_id = target
        if not bot_hash or not tg_chat_id:
            return

        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return
        bot = await cls._get_bot(bot_cfg.token)
        await bot.send_message(chat_id=_tg_chat_id_cast(tg_chat_id), text=text)
