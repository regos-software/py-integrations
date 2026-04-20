# telegram_bot_crm_channel

Telegram CRM channel integration for one Telegram bot per connected integration.

## Webhooks

CRM webhooks consumed by this integration:

- `ChatMessageAdded`
- `ChatMessageEdited`
- `ChatMessageDeleted`
- `ChatWriting`
- `TicketClosed`

Telegram update types consumed by this integration:

- `message`
- `business_message`
- `edited_message`
- `edited_business_message`
- `deleted_business_messages`

## Settings

Required settings:

- `bot_1_token` (string): Telegram bot token from `@BotFather`.
- `bot_1_channel_id` (int): CRM channel id for this bot.

Optional settings:

- `bot_1_lead_subject_template` (string): subject template for new ticket (default: `{display_name}`).
- `bot_1_default_responsible_user_id` (int): default responsible user for newly created ticket.
- `telegram_secret_token` (string): secret token validation for Telegram webhooks.
- `lead_dedupe_ttl_sec` (int): dedupe TTL for inbound events.
- `state_ttl_sec` (int): cache/state TTL.
- `send_private_messages` (bool): forward CRM private messages to Telegram.
- `forward_system_messages` (bool): forward CRM system messages to Telegram.
- `lead_closed_message_template` (string): text sent to Telegram user on `TicketClosed`.
- `phone_request_text` (string): prompt text for phone request flow.
- `phone_share_button_text` (string): Telegram contact-share button label.

Global setting (service-level, not integration setting):

- `app_settings.telegram_update_mode`: `webhook` or `longpolling`.

## Routing model (ticket-only)

- Telegram client id is stored in CRM client field `field_telegram_id`.
- Open ticket lookup uses `Ticket/Get` with filter `external_dialog_id = <telegram_chat_id>`.
- If no open ticket exists for that dialog and channel, a new ticket is created.
- Outbound CRM events are routed to the exact bot by:
  1. `Chat/Get` -> resolve linked `ticket_id`
  2. `Ticket/Get` -> read `channel_id` and `external_dialog_id`
  3. route by `channel_id` to the configured bot slot

This prevents sending one CRM message to all Telegram bots when multiple integrations are active.

## Setup

1. Create a Telegram bot in `@BotFather`.
2. Start chat with the bot from a user account (`/start`).
3. Fill CRM integration settings (`bot_1_token`, `bot_1_channel_id`, optional fields).
4. Connect the integration.
5. Verify flows:
   - Telegram -> CRM message appears in the ticket chat.
   - CRM -> Telegram reply is delivered to the same user/chat.
   - Edit/delete events are synchronized.
