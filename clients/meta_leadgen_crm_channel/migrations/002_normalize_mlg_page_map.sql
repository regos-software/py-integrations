-- Keep mlg_page_map as a route map only. Meta authorization data is stored in
-- REGOS connected integration settings.
ALTER TABLE `mlg_page_map`
    DROP COLUMN IF EXISTS `page_name`,
    DROP COLUMN IF EXISTS `page_access_token`,
    DROP COLUMN IF EXISTS `access_token_expires_at`;
