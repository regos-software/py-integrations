from __future__ import annotations

import html
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlencode

from core.logger import setup_logger


logger = setup_logger("instagram_crm_channel.ui")

_BASE_DIR = Path(__file__).resolve().parent
_TEMPLATE_PATH = _BASE_DIR / "ui_template.html"
_CSS_PATH = _BASE_DIR / "ui_template.css"
_I18N_DIR = _BASE_DIR / "i18n"
_SUPPORTED_LOCALES = ("ru", "uz", "en")
_DEFAULT_LOCALE = "ru"


@dataclass(frozen=True)
class InstagramUiContext:
    connected_integration_id: str
    locale: str = _DEFAULT_LOCALE
    mode: str = "disconnected"
    authorization_url: str = ""
    username: Optional[str] = None
    message_key: str = ""
    message: str = ""
    disconnect_token: str = ""


def normalize_locale(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("_", "-")
    if not raw:
        return _DEFAULT_LOCALE
    primary = raw.split("-", 1)[0]
    return primary if primary in _SUPPORTED_LOCALES else _DEFAULT_LOCALE


def resolve_locale(envelope: Dict[str, Any]) -> str:
    query = envelope.get("query") if isinstance(envelope.get("query"), dict) else {}
    for key in ("lang", "locale", "language", "hl"):
        value = query.get(key)
        if isinstance(value, list):
            value = value[0] if value else None
        if value:
            return normalize_locale(value)

    headers = envelope.get("headers") if isinstance(envelope.get("headers"), dict) else {}
    for header_name, header_value in headers.items():
        if str(header_name or "").lower() != "accept-language":
            continue
        for part in str(header_value or "").split(","):
            lang = normalize_locale(part.split(";", 1)[0])
            if lang:
                return lang
    return _DEFAULT_LOCALE


@lru_cache(maxsize=1)
def _load_template() -> str:
    try:
        return _TEMPLATE_PATH.read_text(encoding="utf-8")
    except Exception as error:
        logger.exception("Failed to load Instagram UI template: %s", error)
        return "<!doctype html><html><body>{content_html}</body></html>"


@lru_cache(maxsize=1)
def _load_css() -> str:
    try:
        return _CSS_PATH.read_text(encoding="utf-8")
    except Exception as error:
        logger.exception("Failed to load Instagram UI CSS: %s", error)
        return "body{margin:0;font-family:Arial,sans-serif;background:#f5f7fb;color:#172033}"


@lru_cache(maxsize=1)
def _load_i18n_bundle() -> Dict[str, Dict[str, str]]:
    bundle: Dict[str, Dict[str, str]] = {}
    for locale in _SUPPORTED_LOCALES:
        path = _I18N_DIR / f"{locale}.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("i18n file must contain an object")
            bundle[locale] = {str(key): str(value) for key, value in payload.items()}
        except Exception as error:
            logger.exception("Failed to load Instagram UI i18n file %s: %s", path, error)
            bundle[locale] = {}

    fallback = bundle.get("ru") or bundle.get("en") or {}
    for locale in _SUPPORTED_LOCALES:
        if not bundle.get(locale):
            bundle[locale] = dict(fallback)
    return bundle


def t(locale: str, key: str, **params: Any) -> str:
    normalized_locale = normalize_locale(locale)
    bundle = _load_i18n_bundle()
    text = (
        bundle.get(normalized_locale, {}).get(key)
        or bundle.get(_DEFAULT_LOCALE, {}).get(key)
        or bundle.get("en", {}).get(key)
        or key
    )
    if params:
        try:
            return text.format(**params)
        except Exception:
            return text
    return text


def ui_url(
    connected_integration_id: str,
    locale: str,
    *,
    action: str = "",
    token: str = "",
) -> str:
    params = {
        "ci": str(connected_integration_id or "").strip(),
        "lang": normalize_locale(locale),
    }
    if action:
        params["action"] = str(action)
    if token:
        params["token"] = str(token)
    return "?" + urlencode(params)


def _escape(value: Any, *, quote: bool = False) -> str:
    return html.escape(str(value or ""), quote=quote)


def _account_label(locale: str, username: Optional[str], *, connected: bool) -> str:
    name = str(username or "").strip()
    if name:
        return f"@{name.lstrip('@')}"
    return t(locale, "account_connected_fallback" if connected else "account_not_connected")


def _language_links(ctx: InstagramUiContext) -> str:
    links = []
    for locale in _SUPPORTED_LOCALES:
        active = " is-active" if normalize_locale(ctx.locale) == locale else ""
        label = t(ctx.locale, f"language_{locale}")
        links.append(
            f'<a class="language-link{active}" href="{_escape(ui_url(ctx.connected_integration_id, locale), quote=True)}">'
            f"{_escape(label)}</a>"
        )
    return "".join(links)


def _list_html(locale: str, keys: Iterable[str]) -> str:
    items = "".join(f"<li>{_escape(t(locale, key))}</li>" for key in keys)
    return f"<ul class=\"steps\">{items}</ul>" if items else ""


def _button(label: str, href: str, *, tone: str = "primary") -> str:
    return f'<a class="button {tone}" href="{_escape(href, quote=True)}">{_escape(label)}</a>'


def _mode_data(ctx: InstagramUiContext) -> Dict[str, Any]:
    locale = normalize_locale(ctx.locale)
    mode = str(ctx.mode or "").strip() or "disconnected"
    connected = mode in {"connected", "connected_success", "confirm_disconnect"}
    account = _account_label(locale, ctx.username, connected=connected)

    data: Dict[str, Any] = {
        "mode": mode,
        "tone": "neutral",
        "badge_key": "badge_disconnected",
        "heading_key": "heading_disconnected",
        "lead_key": "lead_disconnected",
        "account": account,
        "notice_key": "",
        "steps": ("step_save_settings", "step_connect_account", "step_send_test_message"),
        "actions": [],
    }

    if mode == "connected":
        data.update(
            tone="success",
            badge_key="badge_connected",
            heading_key="heading_connected",
            lead_key="lead_connected",
            steps=("step_connected_messages", "step_connected_reply", "step_connected_disconnect"),
            actions=[
                _button(t(locale, "action_disconnect"), ui_url(ctx.connected_integration_id, locale, action="confirm_disconnect"), tone="danger-secondary")
            ],
        )
    elif mode == "connected_success":
        data.update(
            tone="success",
            badge_key="badge_connected",
            heading_key="heading_connected_success",
            lead_key="lead_connected_success",
            notice_key="notice_connected_success",
            steps=("step_connected_messages", "step_connected_reply", "step_connected_disconnect"),
            actions=[
                _button(t(locale, "action_done"), ui_url(ctx.connected_integration_id, locale), tone="primary"),
            ],
        )
    elif mode == "confirm_disconnect":
        data.update(
            tone="warning",
            badge_key="badge_connected",
            heading_key="heading_confirm_disconnect",
            lead_key="lead_confirm_disconnect",
            notice_key="notice_confirm_disconnect",
            steps=("step_disconnect_stop", "step_disconnect_history", "step_disconnect_reconnect"),
            actions=[
                _button(
                    t(locale, "action_confirm_disconnect"),
                    ui_url(
                        ctx.connected_integration_id,
                        locale,
                        action="disconnect",
                        token=ctx.disconnect_token,
                    ),
                    tone="danger",
                ),
                _button(t(locale, "action_cancel"), ui_url(ctx.connected_integration_id, locale), tone="secondary"),
            ],
        )
    elif mode == "disconnected_success":
        data.update(
            tone="neutral",
            badge_key="badge_disconnected",
            heading_key="heading_disconnected_success",
            lead_key="lead_disconnected_success",
            notice_key="notice_disconnected_success",
        )
    elif mode == "conflict":
        actions = []
        if ctx.username:
            actions.append(
                _button(
                    t(locale, "action_disconnect"),
                    ui_url(ctx.connected_integration_id, locale, action="confirm_disconnect"),
                    tone="danger-secondary",
                )
            )
        if ctx.authorization_url:
            actions.append(_button(t(locale, "action_connect"), ctx.authorization_url, tone="primary"))
        data.update(
            tone="warning",
            badge_key="badge_attention",
            heading_key="heading_conflict",
            lead_key="lead_conflict",
            notice_key="notice_conflict",
            steps=("step_conflict_other", "step_conflict_disconnect", "step_conflict_choose"),
            actions=actions,
        )
    elif mode == "error":
        data.update(
            tone="danger",
            badge_key="badge_attention",
            heading_key="heading_error",
            lead_key="lead_error",
            notice_key=ctx.message_key or "notice_error",
            steps=("step_error_settings", "step_error_retry", "step_error_admin"),
        )
    elif mode in {"inactive", "missing_context", "unavailable", "oauth_error", "session_expired"}:
        data.update(
            tone="warning",
            badge_key="badge_attention",
            heading_key=f"heading_{mode}",
            lead_key=f"lead_{mode}",
            notice_key=ctx.message_key,
            steps=("step_error_settings", "step_error_retry", "step_error_admin"),
        )
    else:
        if ctx.authorization_url:
            data["actions"] = [_button(t(locale, "action_connect"), ctx.authorization_url, tone="primary")]

    if mode in {"disconnected", "disconnected_success", "conflict", "error", "unavailable", "oauth_error", "session_expired"}:
        if ctx.authorization_url:
            current_actions = list(data.get("actions") or [])
            if not current_actions:
                data["actions"] = [_button(t(locale, "action_connect"), ctx.authorization_url, tone="primary")]
            else:
                data["actions"] = current_actions
        elif not data["actions"]:
            data["actions"] = [f'<span class="button disabled">{_escape(t(locale, "action_connect_unavailable"))}</span>']

    if ctx.message:
        data["notice_text"] = ctx.message
    return data


def render_instagram_ui(ctx: InstagramUiContext) -> str:
    locale = normalize_locale(ctx.locale)
    data = _mode_data(ctx)
    title = t(locale, "title")
    notice_html = ""
    notice_text = str(data.get("notice_text") or "").strip()
    notice_key = str(data.get("notice_key") or "").strip()
    if notice_text or notice_key:
        text = notice_text or t(locale, notice_key)
        notice_html = f'<div class="notice">{_escape(text)}</div>'

    actions_html = "".join(data.get("actions") or [])
    if not actions_html:
        actions_html = f'<span class="button disabled">{_escape(t(locale, "action_no_action"))}</span>'

    account_label = _escape(str(data.get("account") or ""))
    template = _load_template()
    return template.format(
        safe_lang=_escape(locale, quote=True),
        safe_title=_escape(title),
        style_block=f"<style>\n{_load_css()}\n</style>",
        safe_mode=_escape(str(data.get("mode") or ""), quote=True),
        safe_tone=_escape(str(data.get("tone") or "neutral"), quote=True),
        language_links=_language_links(ctx),
        safe_badge=_escape(t(locale, str(data.get("badge_key") or ""))),
        safe_heading=_escape(t(locale, str(data.get("heading_key") or ""))),
        safe_lead=_escape(t(locale, str(data.get("lead_key") or ""))),
        safe_account_label=account_label,
        safe_account_caption=_escape(t(locale, "account_caption")),
        notice_html=notice_html,
        actions_html=actions_html,
        steps_html=_list_html(locale, data.get("steps") or ()),
    )
