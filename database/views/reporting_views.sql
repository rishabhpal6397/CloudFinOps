-- ============================================================
-- CloudFinOps – Reporting views for Power BI and the REST API
-- All views are idempotent (CREATE OR REPLACE).
-- ============================================================

USE cloudfinops;

-- ============================================================
-- 1. DAILY / MONTHLY TRENDS
-- ============================================================

CREATE OR REPLACE VIEW vw_daily_cost AS
SELECT
    d.date_key,
    d.full_date,
    d.`year`,
    d.`quarter`,
    d.`month`,
    d.`year_month`,
    d.day_name,
    d.is_weekend,
    COUNT(*)                      AS record_count,
    ROUND(SUM(f.cost), 2)         AS total_cost,
    ROUND(AVG(f.cost), 4)         AS avg_record_cost
FROM fact_cost f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.date_key, d.full_date, d.`year`, d.`quarter`,
         d.`month`, d.`year_month`, d.day_name, d.is_weekend;

CREATE OR REPLACE VIEW vw_monthly_cost AS
WITH monthly AS (
    SELECT
        d.`year`,
        d.`month`,
        d.`year_month`,
        COUNT(*)              AS record_count,
        ROUND(SUM(f.cost), 2) AS total_cost
    FROM fact_cost f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.`year`, d.`month`, d.`year_month`
)
SELECT
    m.`year`,
    m.`month`,
    m.`year_month`,
    m.record_count,
    m.total_cost,
    LAG(m.total_cost) OVER (ORDER BY m.`year`, m.`month`) AS prev_month_cost,
    ROUND(m.total_cost - LAG(m.total_cost) OVER (ORDER BY m.`year`, m.`month`), 2) AS mom_change,
    ROUND(
        CASE
            WHEN LAG(m.total_cost) OVER (ORDER BY m.`year`, m.`month`) IS NULL THEN NULL
            WHEN LAG(m.total_cost) OVER (ORDER BY m.`year`, m.`month`) = 0     THEN NULL
            ELSE 100.0 * (m.total_cost - LAG(m.total_cost) OVER (ORDER BY m.`year`, m.`month`))
                 / LAG(m.total_cost) OVER (ORDER BY m.`year`, m.`month`)
        END, 2) AS mom_change_pct
FROM monthly m;

-- ============================================================
-- 2. DIMENSION x MONTH  (stacked charts in Power BI)
-- ============================================================

CREATE OR REPLACE VIEW vw_provider_monthly AS
SELECT
    d.`year_month`,
    p.provider_name,
    ROUND(SUM(f.cost), 2) AS total_cost
FROM fact_cost f
JOIN dim_date d     ON f.date_key     = d.date_key
JOIN dim_provider p ON f.provider_key = p.provider_key
GROUP BY d.`year_month`, p.provider_name;

CREATE OR REPLACE VIEW vw_service_monthly AS
SELECT
    d.`year_month`,
    s.service_name,
    s.service_category,
    ROUND(SUM(f.cost), 2) AS total_cost
FROM fact_cost f
JOIN dim_date d    ON f.date_key    = d.date_key
JOIN dim_service s ON f.service_key = s.service_key
GROUP BY d.`year_month`, s.service_name, s.service_category;

CREATE OR REPLACE VIEW vw_team_monthly AS
SELECT
    d.`year_month`,
    t.team_name,
    ROUND(SUM(f.cost), 2) AS total_cost
FROM fact_cost f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_team t ON f.team_key = t.team_key
GROUP BY d.`year_month`, t.team_name;

CREATE OR REPLACE VIEW vw_environment_monthly AS
SELECT
    d.`year_month`,
    e.environment_name,
    ROUND(SUM(f.cost), 2) AS total_cost
FROM fact_cost f
JOIN dim_date d        ON f.date_key        = d.date_key
JOIN dim_environment e ON f.environment_key = e.environment_key
GROUP BY d.`year_month`, e.environment_name;

-- ============================================================
-- 3. TOTALS BY DIMENSION  (pie / bar charts)
-- ============================================================

CREATE OR REPLACE VIEW vw_cost_by_provider AS
WITH totals AS (SELECT SUM(cost) AS grand_total FROM fact_cost)
SELECT
    p.provider_key,
    p.provider_name,
    p.provider_display,
    COUNT(*)                                       AS record_count,
    ROUND(SUM(f.cost), 2)                          AS total_cost,
    ROUND(100.0 * SUM(f.cost) / t.grand_total, 2)  AS pct_of_total
FROM fact_cost f
JOIN dim_provider p ON f.provider_key = p.provider_key
CROSS JOIN totals t
GROUP BY p.provider_key, p.provider_name, p.provider_display, t.grand_total;

CREATE OR REPLACE VIEW vw_cost_by_service AS
SELECT
    s.service_key,
    s.service_name,
    s.service_category,
    COUNT(*)              AS record_count,
    ROUND(SUM(f.cost), 2) AS total_cost,
    ROUND(AVG(f.cost), 4) AS avg_record_cost
FROM fact_cost f
JOIN dim_service s ON f.service_key = s.service_key
GROUP BY s.service_key, s.service_name, s.service_category;

CREATE OR REPLACE VIEW vw_cost_by_team AS
WITH totals AS (SELECT SUM(cost) AS grand_total FROM fact_cost)
SELECT
    t.team_key,
    t.team_name,
    COUNT(*)                                       AS record_count,
    ROUND(SUM(f.cost), 2)                          AS total_cost,
    ROUND(100.0 * SUM(f.cost) / tot.grand_total,2) AS pct_of_total
FROM fact_cost f
JOIN dim_team t ON f.team_key = t.team_key
CROSS JOIN totals tot
GROUP BY t.team_key, t.team_name, tot.grand_total;

CREATE OR REPLACE VIEW vw_cost_by_environment AS
WITH totals AS (SELECT SUM(cost) AS grand_total FROM fact_cost)
SELECT
    e.environment_key,
    e.environment_name,
    COUNT(*)                                       AS record_count,
    ROUND(SUM(f.cost), 2)                          AS total_cost,
    ROUND(100.0 * SUM(f.cost) / tot.grand_total,2) AS pct_of_total
FROM fact_cost f
JOIN dim_environment e ON f.environment_key = e.environment_key
CROSS JOIN totals tot
GROUP BY e.environment_key, e.environment_name, tot.grand_total;

CREATE OR REPLACE VIEW vw_cost_by_region AS
SELECT
    rg.region_key,
    rg.region_code,
    COUNT(*)              AS record_count,
    ROUND(SUM(f.cost), 2) AS total_cost
FROM fact_cost f
JOIN dim_region rg ON f.region_key = rg.region_key
GROUP BY rg.region_key, rg.region_code;

CREATE OR REPLACE VIEW vw_cost_by_account AS
SELECT
    a.account_key,
    a.account_id,
    p.provider_name,
    COUNT(*)              AS record_count,
    ROUND(SUM(f.cost), 2) AS total_cost
FROM fact_cost f
JOIN dim_account  a ON f.account_key  = a.account_key
JOIN dim_provider p ON a.provider_key = p.provider_key
GROUP BY a.account_key, a.account_id, p.provider_name;

CREATE OR REPLACE VIEW vw_cost_by_resource AS
SELECT
    r.resource_key,
    r.resource_id,
    r.resource_name,
    p.provider_name,
    s.service_name,
    s.service_category,
    t.team_name,
    e.environment_name,
    COUNT(*)              AS record_count,
    ROUND(SUM(f.cost), 2) AS total_cost
FROM fact_cost f
JOIN dim_resource    r ON f.resource_key    = r.resource_key
JOIN dim_provider    p ON f.provider_key    = p.provider_key
JOIN dim_service     s ON f.service_key     = s.service_key
JOIN dim_team        t ON f.team_key        = t.team_key
JOIN dim_environment e ON f.environment_key = e.environment_key
GROUP BY r.resource_key, r.resource_id, r.resource_name,
         p.provider_name, s.service_name, s.service_category,
         t.team_name, e.environment_name;

-- ============================================================
-- 4. DETAIL (drill-down; 119K rows — use with filters)
-- ============================================================

CREATE OR REPLACE VIEW vw_cost_detail AS
SELECT
    f.cost_key,
    f.date_key,
    d.full_date,
    d.`year`,
    d.`quarter`,
    d.`month`,
    d.`year_month`,
    d.day_name,
    d.is_weekend,
    p.provider_name,
    p.provider_display,
    a.account_id,
    s.service_name,
    s.service_category,
    rg.region_code,
    t.team_name,
    e.environment_name,
    r.resource_id,
    r.resource_name,
    f.usage_quantity,
    f.usage_unit,
    f.cost,
    f.currency,
    f.cost_per_unit,
    JSON_UNQUOTE(JSON_EXTRACT(f.tags, '$.env'))         AS tag_env,
    JSON_UNQUOTE(JSON_EXTRACT(f.tags, '$.team'))        AS tag_team,
    JSON_UNQUOTE(JSON_EXTRACT(f.tags, '$.cost_center')) AS tag_cost_center,
    JSON_UNQUOTE(JSON_EXTRACT(f.tags, '$.owner'))       AS tag_owner
FROM fact_cost f
JOIN dim_date        d  ON f.date_key        = d.date_key
JOIN dim_provider    p  ON f.provider_key    = p.provider_key
JOIN dim_account     a  ON f.account_key     = a.account_key
JOIN dim_service     s  ON f.service_key     = s.service_key
JOIN dim_region      rg ON f.region_key      = rg.region_key
JOIN dim_team        t  ON f.team_key        = t.team_key
JOIN dim_environment e  ON f.environment_key = e.environment_key
JOIN dim_resource    r  ON f.resource_key    = r.resource_key;

-- ============================================================
-- 5. LONG-FORMAT VIEW (single dimension-agnostic fact slice)
-- ============================================================

CREATE OR REPLACE VIEW vw_cost_by_dimension_long AS
SELECT 'provider'    AS dimension_type, p.provider_name    AS dimension_value,
       ROUND(SUM(f.cost), 2) AS total_cost, COUNT(*) AS record_count
FROM fact_cost f JOIN dim_provider p    ON f.provider_key = p.provider_key
GROUP BY p.provider_name

UNION ALL
SELECT 'service',     s.service_name,
       ROUND(SUM(f.cost), 2), COUNT(*)
FROM fact_cost f JOIN dim_service s     ON f.service_key = s.service_key
GROUP BY s.service_name

UNION ALL
SELECT 'team',        t.team_name,
       ROUND(SUM(f.cost), 2), COUNT(*)
FROM fact_cost f JOIN dim_team t        ON f.team_key = t.team_key
GROUP BY t.team_name

UNION ALL
SELECT 'environment', e.environment_name,
       ROUND(SUM(f.cost), 2), COUNT(*)
FROM fact_cost f JOIN dim_environment e ON f.environment_key = e.environment_key
GROUP BY e.environment_name

UNION ALL
SELECT 'region',      rg.region_code,
       ROUND(SUM(f.cost), 2), COUNT(*)
FROM fact_cost f JOIN dim_region rg     ON f.region_key = rg.region_key
GROUP BY rg.region_code

UNION ALL
SELECT 'account',     a.account_id,
       ROUND(SUM(f.cost), 2), COUNT(*)
FROM fact_cost f JOIN dim_account a     ON f.account_key = a.account_key
GROUP BY a.account_id;

-- ============================================================
-- 6. KPI SNAPSHOT (one row)
-- ============================================================

CREATE OR REPLACE VIEW vw_kpi_summary AS
WITH monthly AS (
    SELECT d.`year_month`, SUM(f.cost) AS month_cost
    FROM fact_cost f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.`year_month`
),
ranked AS (
    SELECT `year_month`, month_cost,
           ROW_NUMBER() OVER (ORDER BY `year_month` DESC) AS rn
    FROM monthly
),
latest   AS (SELECT `year_month`, month_cost FROM ranked WHERE rn = 1),
previous AS (SELECT `year_month`, month_cost FROM ranked WHERE rn = 2),
totals   AS (SELECT SUM(cost) AS all_time_cost, COUNT(*) AS all_records FROM fact_cost)
SELECT
    ROUND(totals.all_time_cost, 2)     AS total_cost_all_time,
    totals.all_records                 AS total_records,
    latest.`year_month`                  AS latest_month,
    ROUND(latest.month_cost, 2)        AS latest_month_cost,
    previous.`year_month`                AS previous_month,
    ROUND(previous.month_cost, 2)      AS previous_month_cost,
    ROUND(latest.month_cost - previous.month_cost, 2) AS mom_change_amount,
    ROUND(
        CASE WHEN previous.month_cost > 0
             THEN 100.0 * (latest.month_cost - previous.month_cost) / previous.month_cost
             ELSE NULL
        END, 2)                        AS mom_change_pct
FROM totals
CROSS JOIN latest
CROSS JOIN previous;

-- ============================================================
-- 7. LATER-PHASE VIEWS (empty until those phases populate them)
-- ============================================================

CREATE OR REPLACE VIEW vw_anomalies AS
SELECT
    ca.anomaly_id,
    ca.anomaly_date,
    s.service_name,
    s.service_category,
    r.resource_id,
    r.resource_name,
    ca.expected_cost,
    ca.actual_cost,
    ca.deviation,
    ca.anomaly_score,
    ca.severity,
    ca.detection_method,
    ca.created_at
FROM cost_anomalies ca
LEFT JOIN dim_service  s ON ca.service_key  = s.service_key
LEFT JOIN dim_resource r ON ca.resource_key = r.resource_key;

CREATE OR REPLACE VIEW vw_forecasts AS
SELECT
    cf.forecast_id,
    cf.forecast_date,
    cf.generated_on,
    cf.forecast_period,
    s.service_name,
    s.service_category,
    t.team_name,
    cf.predicted_cost,
    cf.lower_bound,
    cf.upper_bound,
    cf.model_name,
    cf.created_at
FROM cost_forecasts cf
LEFT JOIN dim_service s ON cf.service_key = s.service_key
LEFT JOIN dim_team    t ON cf.team_key    = t.team_key;

CREATE OR REPLACE VIEW vw_optimization_savings AS
SELECT
    r.category,
    r.priority,
    r.status,
    COUNT(*)                                                   AS recommendation_count,
    ROUND(SUM(COALESCE(r.estimated_monthly_saving, 0)), 2)     AS total_estimated_monthly_saving,
    ROUND(AVG(COALESCE(r.estimated_monthly_saving, 0)), 2)     AS avg_estimated_monthly_saving
FROM optimization_recommendations r
GROUP BY r.category, r.priority, r.status;

CREATE OR REPLACE VIEW vw_budget_vs_actual AS
WITH budget_actuals AS (
    -- Organization scope
    SELECT b.budget_id, SUM(f.cost) AS actual_amount
    FROM budgets b
    JOIN fact_cost f ON f.date_key BETWEEN
        CAST(DATE_FORMAT(b.start_date, '%Y%m%d') AS UNSIGNED)
        AND CAST(DATE_FORMAT(COALESCE(b.end_date, CURDATE()), '%Y%m%d') AS UNSIGNED)
    WHERE b.`scope` = 'ORGANIZATION'
    GROUP BY b.budget_id

    UNION ALL

    -- Team scope
    SELECT b.budget_id, SUM(f.cost) AS actual_amount
    FROM budgets b
    JOIN fact_cost f ON f.date_key BETWEEN
        CAST(DATE_FORMAT(b.start_date, '%Y%m%d') AS UNSIGNED)
        AND CAST(DATE_FORMAT(COALESCE(b.end_date, CURDATE()), '%Y%m%d') AS UNSIGNED)
    JOIN dim_team t ON f.team_key = t.team_key
    WHERE b.`scope` = 'TEAM' AND t.team_name = b.scope_value
    GROUP BY b.budget_id

    UNION ALL

    -- Service scope
    SELECT b.budget_id, SUM(f.cost) AS actual_amount
    FROM budgets b
    JOIN fact_cost f ON f.date_key BETWEEN
        CAST(DATE_FORMAT(b.start_date, '%Y%m%d') AS UNSIGNED)
        AND CAST(DATE_FORMAT(COALESCE(b.end_date, CURDATE()), '%Y%m%d') AS UNSIGNED)
    JOIN dim_service s ON f.service_key = s.service_key
    WHERE b.`scope` = 'SERVICE' AND s.service_name = b.scope_value
    GROUP BY b.budget_id

    UNION ALL

    -- Account scope
    SELECT b.budget_id, SUM(f.cost) AS actual_amount
    FROM budgets b
    JOIN fact_cost f ON f.date_key BETWEEN
        CAST(DATE_FORMAT(b.start_date, '%Y%m%d') AS UNSIGNED)
        AND CAST(DATE_FORMAT(COALESCE(b.end_date, CURDATE()), '%Y%m%d') AS UNSIGNED)
    JOIN dim_account a ON f.account_key = a.account_key
    WHERE b.`scope` = 'ACCOUNT' AND a.account_id = b.scope_value
    GROUP BY b.budget_id
)
SELECT
    b.budget_id,
    b.name                                       AS budget_name,
    b.`scope`                                    AS budget_scope,
    b.scope_value,
    b.`period`                                   AS budget_period,
    b.budget_amount,
    b.currency,
    b.threshold_warning,
    b.threshold_critical,
    b.start_date,
    b.end_date,
    ROUND(COALESCE(a.actual_amount, 0), 2)       AS actual_amount,
    ROUND(
        CASE WHEN b.budget_amount > 0
             THEN 100.0 * COALESCE(a.actual_amount, 0) / b.budget_amount
             ELSE NULL
        END, 2)                                  AS utilization_pct,
    ROUND(b.budget_amount - COALESCE(a.actual_amount, 0), 2) AS remaining_amount,
    CASE
        WHEN b.budget_amount = 0 THEN 'N/A'
        WHEN 100.0 * COALESCE(a.actual_amount, 0) / b.budget_amount >= b.threshold_critical THEN 'CRITICAL'
        WHEN 100.0 * COALESCE(a.actual_amount, 0) / b.budget_amount >= b.threshold_warning  THEN 'WARNING'
        ELSE 'OK'
    END AS status
FROM budgets b
LEFT JOIN budget_actuals a ON b.budget_id = a.budget_id;