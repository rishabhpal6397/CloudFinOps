-- ============================================================
-- CloudFinOps – Fact tables
-- ============================================================

USE cloudfinops;

CREATE TABLE IF NOT EXISTS fact_cost (
    cost_key          BIGINT         NOT NULL AUTO_INCREMENT,
    date_key          INT            NOT NULL,
    provider_key      INT            NOT NULL,
    account_key       INT            NOT NULL,
    service_key       INT            NOT NULL,
    region_key        INT            NOT NULL,
    team_key          INT            NOT NULL,
    environment_key   INT            NOT NULL,
    resource_key      INT            NOT NULL,
    usage_quantity    DECIMAL(18,4)  NOT NULL DEFAULT 0,
    usage_unit        VARCHAR(32)    NOT NULL,
    cost              DECIMAL(14,4)  NOT NULL,
    currency          CHAR(3)        NOT NULL DEFAULT 'USD',
    cost_per_unit     DECIMAL(18,8),
    tags              JSON,
    source_file       VARCHAR(255),
    loaded_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (cost_key),
    KEY idx_fact_cost_date        (date_key),
    KEY idx_fact_cost_provider    (provider_key),
    KEY idx_fact_cost_account     (account_key),
    KEY idx_fact_cost_service     (service_key),
    KEY idx_fact_cost_team        (team_key),
    KEY idx_fact_cost_env         (environment_key),
    KEY idx_fact_cost_resource    (resource_key),
    KEY idx_fact_cost_date_team   (date_key, team_key),
    KEY idx_fact_cost_date_svc    (date_key, service_key),

    CONSTRAINT fk_fact_cost_date         FOREIGN KEY (date_key)        REFERENCES dim_date(date_key),
    CONSTRAINT fk_fact_cost_provider     FOREIGN KEY (provider_key)    REFERENCES dim_provider(provider_key),
    CONSTRAINT fk_fact_cost_account      FOREIGN KEY (account_key)     REFERENCES dim_account(account_key),
    CONSTRAINT fk_fact_cost_service      FOREIGN KEY (service_key)     REFERENCES dim_service(service_key),
    CONSTRAINT fk_fact_cost_region       FOREIGN KEY (region_key)      REFERENCES dim_region(region_key),
    CONSTRAINT fk_fact_cost_team         FOREIGN KEY (team_key)        REFERENCES dim_team(team_key),
    CONSTRAINT fk_fact_cost_environment  FOREIGN KEY (environment_key) REFERENCES dim_environment(environment_key),
    CONSTRAINT fk_fact_cost_resource     FOREIGN KEY (resource_key)    REFERENCES dim_resource(resource_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;