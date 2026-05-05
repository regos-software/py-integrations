# Meta Leadgen CRM Channel

Integration key: `meta_leadgen_crm_channel`

The integration receives Meta Page `leadgen` webhooks, fetches the full lead
payload from Graph API, then creates or updates CRM `Client` and `Lead` records.

## CRM storage policy

The integration creates only one CRM custom field by default:

- entity: `Lead`
- key: `field_meta_lead_ref`
- value format: `v1;page_id=<page_id>;leadgen_id=<leadgen_id>`

This field is used for idempotency through `Lead/Get` filters. Other Meta data
is written into standard CRM fields where possible:

- `Client.name`
- `Client.phone`
- `Client.email`
- `Client.external_id` only when the form has no phone/email
- `Lead.title`
- `Lead.description`
- `Lead.pipeline_id`
- `Lead.stage_id`
- `Lead.responsible_user_id`
- `Lead.participant_user_ids`
- `Lead.amount` only when the form has an `amount` field

The raw form answers are rendered in `Lead.description`. Additional CRM custom
fields are used only when explicitly configured through field mapping settings,
and those fields must already exist.

## Service settings

- `meta_leadgen_app_id`
- `meta_leadgen_app_secret`
- `meta_leadgen_redirect_uri`
- `meta_leadgen_webhook_verify_token`
- `meta_leadgen_graph_version`, default `v20.0`

Redis must be enabled. The integration uses Redis for OAuth state, page reverse
indexes, dedupe, locks, stream queue, retries, DLQ and worker restore.

## Connected integration settings

- `meta_page_id`: optional before OAuth. Required when the authorized account
  has zero or multiple pages.
- `meta_page_name`: filled after OAuth.
- `meta_page_access_token`: filled after OAuth.
- `meta_access_token_expires_at`: filled after OAuth if Meta returns expiry.
- `meta_lead_pipeline_id`: optional CRM Lead pipeline.
- `meta_lead_stage_id`: optional CRM Lead stage.
- `meta_default_responsible_user_id`: optional responsible user.
- `meta_participant_user_ids`: optional comma-separated list or JSON array.
- `meta_lead_title_template`: optional, default `Meta Lead {leadgen_id}`.
- `meta_client_field_mapping`: optional JSON object mapping Meta form keys to
  existing CRM Client field keys.
- `meta_lead_field_mapping`: optional JSON object mapping Meta form keys to
  existing CRM Lead field keys.

Mapping example:

```json
{
  "city": "field_city",
  "leadgen_id": "field_external_source_id"
}
```

Supported synthetic mapping sources: `leadgen_id`, `page_id`, `form_id`,
`created_time`, `lead_ref`. Meta metadata keys such as `ad_id` and
`campaign_id` can also be mapped when returned by Graph API.

## Endpoints

- UI / OAuth callback: `/clients/meta_leadgen_crm_channel`
- Meta webhook verify and events: `/clients/meta_leadgen_crm_channel/external`

## Runtime flow

1. `Connect` validates settings, ensures `field_meta_lead_ref`, stores OAuth URL
   if the page is not authorized, and starts the Redis worker.
2. UI OAuth stores the selected page token and subscribes the page to `leadgen`.
3. Meta `POST` webhook verifies `x-hub-signature-256`, extracts lead events and
   enqueues them by page mapping.
4. Worker fetches full lead details by `leadgen_id`, resolves CRM client, then
   creates or updates the CRM Lead idempotently by `field_meta_lead_ref`.
