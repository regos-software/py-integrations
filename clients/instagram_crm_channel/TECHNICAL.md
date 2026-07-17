# Instagram CRM Channel Technical Notes

## Storage Responsibilities

MariaDB stores only durable routing metadata for the Instagram integration.

- `igc_business_map` keeps `instagram_business_account_id -> connected_integration_id`.
- Redis remains responsible for streams, retries, DLQ, dedupe, locks, OAuth state, short-lived active state, and route caches.
- Runtime settings remain in REGOS connected integration settings.

## Graph API

- `instagram_graph_version` controls the Instagram Graph API version. Default: `v25.0`.
- Before sending CRM messages to Direct, the integration silently refreshes an Instagram long-lived token when it is close to expiry.
- If token refresh or the auth retry fails during outbound Direct delivery, the integration adds a CRM system message to the same chat and acknowledges the stream job to avoid repeated alerts.

## Migrations

Migration files are stored in `clients/instagram_crm_channel/migrations`.

- `001_create_igc_business_map.sql` creates the persistent business mapping table.
- The integration applies these migrations with `CREATE TABLE IF NOT EXISTS` when MariaDB is enabled.
- The table prefix is `igc_`, so the database ownership stays isolated to this integration.

## Stream Model

Instagram uses one Redis stream for all connected integrations:

- `igc:stream`
- `igc:stream:dlq`

Each stream entry carries `connected_integration_id`. Workers load the runtime for that exact connected integration before processing the entry.

## Dialog Rating

Instagram uses the CRM channel rating settings.

- The integration subscribes to `TicketClosed`.
- On ticket close it sends the channel `end_message` and, when enabled, `rating_message` to Instagram Direct.
- A pending rating state is stored in Redis for the exact `connected_integration_id`, Instagram business account, external user, and ticket.
- The next inbound Direct message with text `1`, `2`, `3`, `4`, or `5` is consumed as the ticket rating and is not added as a regular chat message.
- Positive or negative follow-up text is sent from the CRM channel rating settings when configured.
