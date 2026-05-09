-- Persistent Instagram Business Account to connected integration mapping.
-- Queues, retries, dedupe, locks, and transient route caches stay in Redis.
CREATE TABLE IF NOT EXISTS `igc_business_map` (
    `business_id` VARCHAR(128) NOT NULL,
    `connected_integration_id` VARCHAR(128) NOT NULL,
    `username` VARCHAR(255) NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`business_id`),
    KEY `idx_igc_business_map_ci` (`connected_integration_id`),
    KEY `idx_igc_business_map_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
