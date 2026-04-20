# telegram_bot_crm_channel

Telegram CRM channel integration for one Telegram bot per connected integration.

## Webhooks

CRM webhooks consumed by this integration:

- `ChatMessageAdded`
- `ChatMessageEdited`
- `ChatMessageDeleted`
- `ChatWriting`
- `TicketClosed`
- `ChannelEdited`

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
- `phone_request_text` (string): prompt text for phone request flow.
- `phone_share_button_text` (string): Telegram contact-share button label.

Global setting (service-level, not integration setting):

- `app_settings.telegram_update_mode`: `webhook` or `longpolling`.

## Routing model (ticket-only)

- Telegram client id is stored in CRM client field `field_telegram_id`.
- Ticket creation relies on the server invariant: one open ticket per `client_id + channel_id`.
- `Ticket/Add` is treated as idempotent: repeated calls reuse the existing open ticket/chat.
- `external_dialog_id` stores pinned routing metadata in format `ci:<connected_integration_id>:tg:<telegram_chat_id>`.
- For multiple `ConnectedIntegration` with the same CRM channel, outbound CRM replies are sent only by the pinned `connected_integration_id` from `external_dialog_id`.
- Channel messages are used directly:
  - `start_message` is sent to client each time a new ticket is created.
  - `end_message` is sent to client on `TicketClosed`.
- Message formatting supports CRM markdown plus BBCode-like tags (`[B]...[/B]`, `[I]...[/I]`, `[U]...[/U]`, `[S]...[/S]`, `[BR]`).
- Outbound CRM events are routed to the exact bot by:
  1. `Chat/Get` -> resolve linked `ticket_id`
  2. `Ticket/Get` -> read `channel_id` and parse `external_dialog_id`
  3. send only when parsed `connected_integration_id` matches current integration

## Setup

1. Create a Telegram bot in `@BotFather`.
2. Start chat with the bot from a user account (`/start`).
3. Fill CRM integration settings (`bot_1_token`, `bot_1_channel_id`, optional fields).
4. Connect the integration.
5. Verify flows:
   - Telegram -> CRM message appears in the ticket chat.
   - CRM -> Telegram reply is delivered to the same user/chat.
   - Edit/delete events are synchronized.
