-- Persistent Meta Page to connected integration mapping.
-- Streams, retries, dedupe, locks, OAuth state, and transient route caches stay in Redis.
CREATE TABLE IF NOT EXISTS `mlg_page_map` (
    `page_id` VARCHAR(128) NOT NULL,
    `connected_integration_id` VARCHAR(128) NOT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`page_id`),
    KEY `idx_mlg_page_map_ci` (`connected_integration_id`),
    KEY `idx_mlg_page_map_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
