# Power BI Data Model

## Recommended model

Import these as flat tables (they're already pre-aggregated views):

```
┌──────────────────────┐
│  vw_kpi_summary      │  (1 row — used only for KPI cards)
└──────────────────────┘

┌──────────────────────┐       ┌──────────────────────┐
│  vw_daily_cost       │       │  vw_monthly_cost     │
│  (365 rows)          │       │  (12 rows)           │
└──────────────────────┘       └──────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│  vw_provider_monthly │  │  vw_service_monthly  │  │  vw_team_monthly     │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘

┌──────────────────────┐       ┌──────────────────────┐
│  vw_cost_by_service  │       │  vw_cost_by_team     │
│  vw_cost_by_provider │       │  vw_cost_by_region   │
│  vw_cost_by_account  │       │  vw_cost_by_env      │
└──────────────────────┘       └──────────────────────┘
```

## Relationships

The monthly and daily views share `year_month` (as `CHAR(7)`). Because they're
already aggregated, you have two options:

**Option 1 — No relationships (simplest).** Each visual uses its own table.
This is fine for a portfolio project — the KPI summary drives all cards, the
trend views drive their respective visuals.

**Option 2 — Snowflake via a date table.** Create a proper date table:

```dax
Date = 
ADDCOLUMNS(
    CALENDAR(DATE(2024, 10, 1), DATE(2026, 9, 30)),
    "Year", YEAR([Date]),
    "Month", MONTH([Date]),
    "YearMonth", FORMAT([Date], "YYYY-MM"),
    "Quarter", QUARTER([Date]),
    "MonthName", FORMAT([Date], "MMMM"),
    "DayName", FORMAT([Date], "DDDD"),
    "IsWeekend", WEEKDAY([Date], 2) >= 6
)
```

Then relate:
- `Date[Date]` 1 ── * `vw_daily_cost[full_date]`

Mark `Date` as a date table and use it as the axis in all time-series visuals.
This enables MTD/QTD/YTD and year-over-year comparisons (see `dax_measures.md`).

## Column data types (Power BI auto-detects these; verify them)

| Column | Type |
|---|---|
| All `*_key` | Whole number |
| `full_date` | Date |
| `year_month` | Text (don't convert to Date — it's already `YYYY-MM`) |
| All `cost`, `total_cost`, `*_amount` | Decimal number |
| `pct_of_total` | Decimal number (format as %) |
| `record_count`, `rows_returned` | Whole number |
| `is_weekend` | True/False |
| `severity` | Text |

## Refresh strategy

- **Manual refresh:** Re-run `export_for_powerbi.py`, then click **Refresh**.
- **Scheduled:** Publish to Power BI Service, install the on-premises data
  gateway, and configure a scheduled refresh pointing at your CSV folder.

For a portfolio project, manual refresh is plenty — mention in your README that
you understand the production path.