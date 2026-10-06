-- ============================================================
-- CloudFinOps – FinOps tables
-- Populated by later phases (budgets, anomaly detection, etc.)
-- ============================================================

USE cloudfinops;

-- ---------- budgets ----------
CREATE TABLE IF NOT EXISTS budgets (
    budget_id          INT            NOT NULL AUTO_INCREMENT,
    name               VARCHAR(128)   NOT NULL,
    `scope`              ENUM('ORGANIZATION','ACCOUNT','TEAM','SERVICE') NOT NULL,
    scope_value        VARCHAR(128),
    `period`             ENUM('DAILY','WEEKLY','MONTHLY','QUARTERLY','YEARLY') NOT NULL,
    budget_amount      DECIMAL(14,2)  NOT NULL,
    currency           CHAR(3)        NOT NULL DEFAULT 'USD',
    threshold_warning  DECIMAL(5,2)   NOT NULL DEFAULT 80.00,
    threshold_critical DECIMAL(5,2)   NOT NULL DEFAULT 90.00,
    start_date         DATE           NOT NULL,
    end_date           DATE,
    created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (budget_id),
    KEY idx_budgets_scope (`scope`, scope_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- budget_alerts ----------
CREATE TABLE IF NOT EXISTS budget_alerts (
    alert_id      BIGINT        NOT NULL AUTO_INCREMENT,
    budget_id     INT           NOT NULL,
    alert_date    DATE          NOT NULL,
    actual_amount DECIMAL(14,2) NOT NULL,
    threshold_pct DECIMAL(5,2)  NOT NULL,
    severity      ENUM('WARNING','CRITICAL') NOT NULL,
    message       VARCHAR(255),
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (alert_id),
    KEY idx_alert_budget (budget_id),
    KEY idx_alert_date (alert_date),
    CONSTRAINT fk_alert_budget FOREIGN KEY (budget_id) REFERENCES budgets(budget_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- cost_anomalies ----------
CREATE TABLE IF NOT EXISTS cost_anomalies (
    anomaly_id        BIGINT         NOT NULL AUTO_INCREMENT,
    anomaly_date      DATE           NOT NULL,
    service_key       INT,
    resource_key      INT,
    expected_cost     DECIMAL(14,4),
    actual_cost       DECIMAL(14,4),
    deviation         DECIMAL(14,4),
    anomaly_score     DECIMAL(10,4),
    severity          ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL,
    detection_method  VARCHAR(64)    NOT NULL,
    details           JSON,
    created_at        TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (anomaly_id),
    KEY idx_anom_date (anomaly_date),
    KEY idx_anom_severity (severity),
    KEY idx_anom_service (service_key),
    CONSTRAINT fk_anom_service  FOREIGN KEY (service_key)  REFERENCES dim_service(service_key),
    CONSTRAINT fk_anom_resource FOREIGN KEY (resource_key) REFERENCES dim_resource(resource_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- cost_forecasts ----------
CREATE TABLE IF NOT EXISTS cost_forecasts (
    forecast_id       BIGINT         NOT NULL AUTO_INCREMENT,
    forecast_date     DATE           NOT NULL,       -- the date being forecast
    generated_on      DATE           NOT NULL,       -- when the forecast was produced
    forecast_period   VARCHAR(16)    NOT NULL,       -- '7d', '30d', 'next_month'
    service_key       INT,
    team_key          INT,
    predicted_cost    DECIMAL(14,4)  NOT NULL,
    lower_bound       DECIMAL(14,4),
    upper_bound       DECIMAL(14,4),
    model_name        VARCHAR(64)    NOT NULL,
    created_at        TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (forecast_id),
    KEY idx_forecast_date (forecast_date),
    KEY idx_forecast_service (service_key),
    KEY idx_forecast_team (team_key),
    CONSTRAINT fk_forecast_service FOREIGN KEY (service_key) REFERENCES dim_service(service_key),
    CONSTRAINT fk_forecast_team    FOREIGN KEY (team_key)    REFERENCES dim_team(team_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- optimization_recommendations ----------
CREATE TABLE IF NOT EXISTS optimization_recommendations (
    recommendation_id       BIGINT         NOT NULL AUTO_INCREMENT,
    resource_key            INT            NOT NULL,
    category                VARCHAR(32)    NOT NULL,   -- LOW_UTILIZATION, UNUSED, STORAGE, DATABASE
    finding                 TEXT           NOT NULL,
    recommendation          TEXT           NOT NULL,
    estimated_monthly_saving DECIMAL(14,2),
    priority                ENUM('LOW','MEDIUM','HIGH') NOT NULL,
    status                  ENUM('OPEN','IN_REVIEW','IMPLEMENTED','DISMISSED')
                            NOT NULL DEFAULT 'OPEN',
    created_at              TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (recommendation_id),
    KEY idx_rec_status (status),
    KEY idx_rec_priority (priority),
    KEY idx_rec_resource (resource_key),
    CONSTRAINT fk_rec_resource FOREIGN KEY (resource_key) REFERENCES dim_resource(resource_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;