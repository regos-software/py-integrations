# EDO Faktura.uz: technical notes

## External API

- Token endpoint: `https://account.faktura.uz/token`
- API base URL: `https://api.faktura.uz/Api`
- Swagger: `https://api.faktura.uz/swagger/docs/v1`

The integration uses the Faktura.uz password grant for an integration-specific account and caches the access token in Redis for a short time.

## Integration Settings

| Key | Required | Scope | Hide in UI | Description |
|---|---:|---|---:|---|
| `FAKTURA_UZ_CLIENT_ID` | Yes | firm | Yes | Faktura.uz OAuth client id. |
| `FAKTURA_UZ_LOGIN` | Yes | firm | Yes | Faktura.uz account login. |
| `FAKTURA_UZ_PASSWORD` | Yes | firm | Yes | Faktura.uz account password. |
| `FAKTURA_UZ_PRIVATE_KEY` | Yes | firm | Yes | Faktura.uz OAuth client secret/private key. |

## CRM Actions

- `connect`: validates the connected integration and starts Redis stream workers.
- `check`: validates the connected integration and optionally checks Faktura.uz credentials for a firm.
- `get_documents`: reads inbox documents with Faktura.uz pagination.
- `get_document_operations`: loads and maps document rows.
- `import_document`: queues import of one Faktura.uz document into CRM.
- `export_documents`: queues export of CRM invoices to Faktura.uz.

## Faktura.uz Endpoints

- `GET Document/GetDocuments`
  - Uses `companyInn`, `isInbox=true`, document `types`, `statuses`, `limit`, `skip`, and optional invoice date filters.
- `POST Document/GetDocumentsContent`
  - Uses `companyInn` and `DocumentUniqueIds`.
- `POST Document/ImportDocumentRegister`
  - Uses `companyInn` and sends the invoice container.

## Queues and Caches

- Queue: one Redis stream for all connected instances of the integration.
- DLQ: separate Redis stream with the same TTL policy.
- Token cache: Redis key scoped by connected integration and firm.
- Default stream TTL: `86400` seconds.

Redis is used for queueing and short-lived cache only. The integration does not store a permanent mapping in Redis; imported invoices are linked to CRM documents through `DocInvoice/SetExternalData`.

## Idempotency

Before importing an incoming Faktura.uz document, the integration calls `DocInvoice/Get` with `external_code` and the firm id. If a CRM invoice already exists, the import job is treated as completed and no duplicate document is created.
