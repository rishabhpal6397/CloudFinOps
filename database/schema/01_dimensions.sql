-- ============================================================
-- CloudFinOps – Dimension tables (star schema)
-- ============================================================

USE cloudfinops;

-- ---------- dim_date ----------
-- date_key = YYYYMMDD (e.g. 20251001)
CREATE TABLE IF NOT EXISTS dim_date (
    date_key      INT          NOT NULL,
    full_date     DATE         NOT NULL,
    `year`        SMALLINT     NOT NULL,
    `quarter`     TINYINT      NOT NULL,
    `month`       TINYINT      NOT NULL,
    month_name    VARCHAR(12)  NOT NULL,
    `day`         TINYINT      NOT NULL,
    day_of_week   TINYINT      NOT NULL,
    day_name      VARCHAR(12)  NOT NULL,
    is_weekend    BOOLEAN      NOT NULL,
    `year_month`    CHAR(7)      NOT NULL,
    PRIMARY KEY (date_key),
    UNIQUE KEY uq_dim_date_full_date (full_date),
    KEY idx_dim_date_year_month (`year_month`),
    KEY idx_dim_date_year (`year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- dim_provider ----------
CREATE TABLE IF NOT EXISTS dim_provider (
    provider_key       INT          NOT NULL AUTO_INCREMENT,
    provider_name      VARCHAR(32)  NOT NULL,
    provider_display   VARCHAR(64)  NOT NULL,
    PRIMARY KEY (provider_key),
    UNIQUE KEY uq_dim_provider_name (provider_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- dim_account ----------
CREATE TABLE IF NOT EXISTS dim_account (
    account_key   INT          NOT NULL AUTO_INCREMENT,
    account_id    VARCHAR(64)  NOT NULL,
    provider_key  INT          NOT NULL,
    PRIMARY KEY (account_key),
    UNIQUE KEY uq_dim_account_id (account_id),
    KEY idx_dim_account_provider (provider_key),
    CONSTRAINT fk_dim_account_provider
        FOREIGN KEY (provider_key) REFERENCES dim_provider(provider_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- dim_service ----------
CREATE TABLE IF NOT EXISTS dim_service (
    service_key       INT          NOT NULL AUTO_INCREMENT,
    service_name      VARCHAR(64)  NOT NULL,
    service_category  VARCHAR(32)  NOT NULL,
    PRIMARY KEY (service_key),
    UNIQUE KEY uq_dim_service_name (service_name),
    KEY idx_dim_service_category (service_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- dim_region ----------
CREATE TABLE IF NOT EXISTS dim_region (
    region_key   INT          NOT NULL AUTO_INCREMENT,
    region_code  VARCHAR(32)  NOT NULL,
    PRIMARY KEY (region_key),
    UNIQUE KEY uq_dim_region_code (region_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- dim_team ----------
CREATE TABLE IF NOT EXISTS dim_team (
    team_key   INT          NOT NULL AUTO_INCREMENT,
    team_name  VARCHAR(64)  NOT NULL,
    PRIMARY KEY (team_key),
    UNIQUE KEY uq_dim_team_name (team_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- dim_environment ----------
CREATE TABLE IF NOT EXISTS dim_environment (
    environment_key   INT          NOT NULL AUTO_INCREMENT,
    environment_name  VARCHAR(32)  NOT NULL,
    PRIMARY KEY (environment_key),
    UNIQUE KEY uq_dim_environment_name (environment_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- dim_resource ----------
CREATE TABLE IF NOT EXISTS dim_resource (
    resource_key    INT          NOT NULL AUTO_INCREMENT,
    resource_id     VARCHAR(255) NOT NULL,
    resource_name   VARCHAR(255),
    provider_key    INT          NOT NULL,
    PRIMARY KEY (resource_key),
    UNIQUE KEY uq_dim_resource_id (resource_id),
    KEY idx_dim_resource_provider (provider_key),
    CONSTRAINT fk_dim_resource_provider
        FOREIGN KEY (provider_key) REFERENCES dim_provider(provider_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;