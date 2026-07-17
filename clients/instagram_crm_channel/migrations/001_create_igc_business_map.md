# 001_create_igc_business_map

Creates the persistent routing map for Instagram Business Accounts.

## Table

`igc_business_map`

## Columns

- `business_id`: Instagram Business Account identifier from Meta webhook `entry[].id`.
- `connected_integration_id`: REGOS connected integration identifier that owns this Instagram account.
- `username`: optional Instagram username resolved during OAuth.
- `is_active`: active route flag. Disconnect marks existing routes inactive.
- `created_at`: row creation timestamp.
- `updated_at`: last update timestamp.

## Runtime Use

The integration reads this table only when Redis route cache misses. Redis remains the queue and transient cache layer.
