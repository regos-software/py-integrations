# telegram_bot_crm_channel

Telegram <-> REGOS CRM chat bridge with Redis-backed queue workers.

## Required settings

Enable at least one bot (up to 5):

- `BOT_1_ENABLED=true`
- `BOT_1_TOKEN=<telegram_bot_token>`
- `BOT_1_PIPELINE_ID=<lead_pipeline_id>`
- `BOT_1_CHANNEL_ID=<crm_channel_id>`

Repeat for `BOT_2_* ... BOT_5_*` if needed.

## Optional settings

- `BOT_{N}_LEAD_SUBJECT_TEMPLATE`
- `BOT_{N}_DEFAULT_RESPONSIBLE_USER_ID`
- `LEAD_DEDUPE_TTL_SEC` (default `86400`)
- `STATE_TTL_SEC` (default `86400`)
- `TELEGRAM_SECRET_TOKEN`
- `SEND_PRIVATE_MESSAGES` (`false` by default)
- `FORWARD_SYSTEM_MESSAGES` (`false` by default)
- `LEAD_CLOSED_MESSAGE_TEMPLATE`
- `telegram_update_mode` (`webhook` or `longpolling`)

## Notes

- `bot_id` is always `md5(token)`.
- Redis is mandatory (`redis_enabled=true`).
- In longpolling mode only one poller per bot token is active in cluster (`lock:polling_owner:{bot_hash}`).
- In webhook mode pass `bot_hash` in Telegram webhook query string.
