# telegram_bot_crm_channel

Telegram <-> CRM chat bridge in strict single-bot mode (`bot_1_*`).

## What it does

- Receives inbound Telegram messages and writes them to CRM chat.
- Sends outbound CRM chat messages to Telegram.
- Creates a lead on first inbound message and reuses it while open.
- Uses Redis for queueing, dedupe, and mappings.

## Settings source

All keys are read from `ConnectedIntegrationSetting` for integration key
`telegram_bot_crm_channel`.

`telegram_update_mode` is taken only from global config
`app_settings.telegram_update_mode` (not from integration settings).

## Settings

| Key | Required | Allowed values | Default | Description |
|---|---|---|---|---|
| `bot_1_enabled` | Yes | `true` / `false` | `false` | Enables integration. Must be `true` to run. |
| `bot_1_token` | Yes | Telegram bot token | - | Telegram Bot API token. |
| `bot_1_pipeline_id` | Yes | positive integer | - | CRM pipeline id for created leads. |
| `bot_1_channel_id` | Yes | positive integer | - | CRM channel id used in `Lead/Add`. |
| `bot_1_lead_subject_template` | No | `format_map` template | `{display_name}` | Lead subject template. Placeholders: `chat_id`, `first_name`, `last_name`, `username`, `full_name`, `display_name`. |
| `bot_1_default_responsible_user_id` | No | positive integer | empty | `responsible_user_id` in `Lead/Add`. |
| `bot_1_auto_create_contact` | No | `none`, `retail_customer` | `none` | Auto-create contact before `Lead/Add`. |
| `bot_1_retail_customer_group_id` | Conditionally | positive integer | empty | Required when `bot_1_auto_create_contact=retail_customer`. Used as `group_id` for `RetailCustomer/Add`. |
| `telegram_secret_token` | No | non-empty string | empty | Expected `x-telegram-bot-api-secret-token` for Telegram webhook. |
| `lead_dedupe_ttl_sec` | No | integer `>= 60` | `86400` | TTL for inbound dedupe keys. |
| `state_ttl_sec` | No | integer `>= 60` | `86400` | TTL for state keys (locks/cache/mappings). |
| `send_private_messages` | No | `true` / `false` | `false` | Forward CRM `Private` messages to Telegram. |
| `forward_system_messages` | No | `true` / `false` | `false` | Forward CRM `System` messages to Telegram. |
| `lead_closed_message_template` | No | string | empty | Message sent to Telegram on `LeadClosed`. |

## Auto-create contact

When `bot_1_auto_create_contact=retail_customer`:

1. Integration tries to find existing `RetailCustomer` by Telegram id field (`field_telegram_id`).
2. If not found, creates `RetailCustomer` in `bot_1_retail_customer_group_id`.
3. Stores mapping `(connected_integration_id, bot_hash, tg_chat_id) -> customer_id` in Redis.
4. If contact is created, integration sends `System` message: `Создан розничный покупатель: {Имя}`.
5. If existing contact is updated, integration sends `System` message: `Обновлен розничный покупатель: {Имя}`.

If contact create fails, lead flow still continues (best effort).

## Delivery failures

- If outbound delivery to Telegram fails after retries, integration writes a CRM `System` message to the same chat.
- The message contains a human-readable reason in Russian and a short technical reason for debugging.

## Global Config

- `app_settings.telegram_update_mode`: `webhook` or `longpolling`.
- In `webhook` mode `integration_url` must be public HTTPS with DNS resolvable from Telegram.

## CRM webhooks used

- `ChatMessageAdded`
- `ChatMessageEdited`
- `ChatMessageDeleted`
- `ChatWriting`
- `LeadClosed`
