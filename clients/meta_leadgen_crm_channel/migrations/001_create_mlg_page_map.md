# 001_create_mlg_page_map

Creates `mlg_page_map`, the persistent Meta Page to connected integration map.

Redis keeps only transient state for this integration: OAuth state, route cache,
workers, streams, retries, locks, and dedupe keys.
