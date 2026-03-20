# telegram_bot_crm_channel

Telegram <-> REGOS CRM chat bridge with Redis-backed queue workers.

## Required settings

Single-bot mode only:

- `BOT_1_ENABLED=true`
- `BOT_1_TOKEN=<telegram_bot_token>`
- `BOT_1_PIPELINE_ID=<lead_pipeline_id>`
- `BOT_1_CHANNEL_ID=<crm_channel_id>`

## Optional settings

- `BOT_1_LEAD_SUBJECT_TEMPLATE`
- `BOT_1_DEFAULT_RESPONSIBLE_USER_ID`
- `LEAD_DEDUPE_TTL_SEC` (default `86400`)
- `STATE_TTL_SEC` (default `86400`)
- `TELEGRAM_SECRET_TOKEN`
- `SEND_PRIVATE_MESSAGES` (`false` by default)
- `FORWARD_SYSTEM_MESSAGES` (`false` by default)
- `LEAD_CLOSED_MESSAGE_TEMPLATE`
- `telegram_update_mode` (`webhook` or `longpolling`)

## Bot flow (business)

1. A user sends a message to the Telegram bot.
2. The system checks whether this user already has an active CRM lead.
3. If there is no active lead, the system creates a new Lead in the configured pipeline for this bot.
4. During lead creation, the system fills available customer context from Telegram (for example, name and phone if provided), so operators see who started the dialog.
5. The new lead is linked to this Telegram dialog, so all next messages from this user continue in the same lead until it is closed.
6. The first user message is added to the CRM chat linked to that lead.
7. An operator replies in the CRM chat, and the reply is delivered to Telegram.
8. The dialog continues in both directions: Telegram <-> CRM chat.
9. When the lead is closed in CRM, the user can receive a final message.

Telegram inbound event handling:

- `message` and `business_message` -> `ChatMessage/Add` in CRM.
- `edited_message` and `edited_business_message` -> `ChatMessage/Edit` in CRM.
- `deleted_business_messages` (and compatible `deleted_*` payloads) -> `ChatMessage/Delete` in CRM when message mapping is available.
- For existing leads, inbound Telegram messages trigger best-effort `Lead/Edit` to refresh contact fields (`client_name`, `client_phone`, `external_*`, `bot_id`) and fill `client_avatar_url` when it is empty.

Delivery issue alerts:

- If outbound Telegram delivery fails after all retries, integration posts an internal alert message to the related CRM chat.

## Webhooks

REGOS webhooks subscribed by integration:

- `ChatMessageAdded`
- `ChatMessageEdited`
- `ChatMessageDeleted`
- `ChatWriting`
- `LeadClosed`

Telegram webhook endpoint format (when `telegram_update_mode=webhook`):

- `/external/{connected_integration_id}/external/`
- optional backward-compatible query: `?bot_hash=<md5(BOT_1_TOKEN)>`
- if `TELEGRAM_SECRET_TOKEN` is configured, header `x-telegram-bot-api-secret-token` is validated.

## Notes

- `bot_id` is always `md5(token)`.
- Integration supports exactly one bot (`BOT_1_*`).
- Redis is mandatory (`redis_enabled=true`).
- In longpolling mode only one poller per bot token is active in cluster (`lock:polling_owner:{bot_hash}`).
- In webhook mode `bot_hash` query is optional and used only for backward compatibility.
- Media transfer:
  - Telegram -> CRM: `photo`, `document`, `audio`, `voice`.
  - CRM -> Telegram: images are sent as photo, audio as audio/voice, other files as document.
