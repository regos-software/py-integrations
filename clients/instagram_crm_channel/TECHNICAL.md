# Instagram CRM Channel Technical Notes

## Storage Responsibilities

MariaDB stores only durable routing metadata for the Instagram integration.

- `igc_business_map` keeps `instagram_business_account_id -> connected_integration_id`.
- Redis remains responsible for streams, retries, DLQ, dedupe, locks, OAuth state, short-lived active state, and route caches.
- Runtime settings remain in REGOS connected integration settings.

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
