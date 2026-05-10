from __future__ import annotations

from config.settings import settings as app_settings


class MetaLeadgenCrmChannelConfig:
    INTEGRATION_KEY = "meta_leadgen_crm_channel"
    REDIS_PREFIX = "mlg:"

    GRAPH_API_VERSION = str(
        getattr(app_settings, "meta_leadgen_graph_version", "") or "v20.0"
    ).strip()
    GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
    OAUTH_DIALOG_URL = f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth"
    OAUTH_TOKEN_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token"

    OAUTH_SCOPES = (
        "pages_show_list",
        "pages_read_engagement",
        "leads_retrieval",
    )

    SETTINGS_TTL_SEC = max(int(app_settings.redis_cache_ttl or 60), 60)
    MAP_TTL_SEC = 30 * 24 * 60 * 60
    DEDUPE_TTL_SEC = 60 * 60
    LOCK_TTL_SEC = 60
    OAUTH_STATE_TTL_SEC = 10 * 60
    FIELD_CACHE_TTL_SEC = 10 * 60
    ACTIVE_CACHE_TTL_SEC = 30
    HTTP_TIMEOUT_SEC = 30
    STREAM_GROUP = "meta_leadgen_crm_channel_workers"
    STREAM_TTL_SEC = 24 * 60 * 60
    STREAM_MAXLEN = 10000
    STREAM_BATCH_SIZE = 10
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_MAX_RETRIES = 3
    ACTIVE_CI_IDS_TTL_SEC = 7 * 24 * 60 * 60
    WORKER_HEARTBEAT_TTL_SEC = 60

    LEAD_REF_FIELD_KEY = "meta_lead_ref"
    LEAD_REF_FIELD_FULL_KEY = "field_meta_lead_ref"
    LEAD_REF_FIELD_NAME = "Meta Lead Reference"
    LEAD_REF_FIELD_ENTITY_TYPE = "Lead"
    LEAD_REF_FIELD_DATA_TYPE = "string"

    MAX_DESCRIPTION_CHARS = 6000
    MAX_FIELD_VALUE_CHARS = 2000

    SETTING_PAGE_ID = "meta_page_id"
    SETTING_PAGE_NAME = "meta_page_name"
    SETTING_PAGE_ACCESS_TOKEN = "meta_page_access_token"
    SETTING_ACCESS_TOKEN_EXPIRES_AT = "meta_access_token_expires_at"
    SETTING_PIPELINE_ID = "meta_lead_pipeline_id"
    SETTING_STAGE_ID = "meta_lead_stage_id"
    SETTING_RESPONSIBLE_USER_ID = "meta_default_responsible_user_id"
    SETTING_PARTICIPANT_USER_IDS = "meta_participant_user_ids"
    SETTING_TITLE_TEMPLATE = "meta_lead_title_template"
    SETTING_CLIENT_FIELD_MAPPING = "meta_client_field_mapping"
    SETTING_LEAD_FIELD_MAPPING = "meta_lead_field_mapping"
    SETTING_AUTHORIZATION_URL = "meta_authorization_url"
    SETTING_AUTHORIZATION_URL_GENERATED_AT = "meta_authorization_url_generated_at"
    SETTING_AUTHORIZATION_STATUS = "meta_authorization_status"
    SETTING_AUTHORIZED = "meta_authorized"

    DEFAULT_TITLE_TEMPLATE = "Meta Lead {leadgen_id}"
