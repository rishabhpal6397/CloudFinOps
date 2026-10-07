# Power BI Report Page Designs

7 pages. Build them in this order.

---

## Page 1 — Executive Overview

**Purpose:** One-glance health check for leadership.

**Layout (1920×1080 canvas):**

```
┌─────────────────────────────────────────────────────────────────────┐
│  CloudFinOps — Executive Overview              [Date slicer]        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ Total   │ │ Latest  │ │  MoM    │ │ Average │ │Projected│        │
│  │ Cost    │ │ Month   │ │ Change% │ │  Daily  │ │ Annual  │        │
│  │ $26.4M  │ │ $2.36M  │ │ +1.47%  │ │ $72.4K  │ │ $26.4M  │        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────┐ ┌──────────────────────────┐  │
│  │                                  │ │                          │  │
│  │   Daily Cost Trend (line)        │ │  Cost by Provider        │  │
│  │   (vw_daily_cost)                │ │  (donut, vw_cost_by_     │  │
│  │                                  │ │   provider)              │  │
│  │                                  │ │                          │  │
│  └──────────────────────────────────┘ └──────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────┐ ┌──────────────────────────┐  │
│  │  Monthly Cost by Provider        │ │  Top 5 Services by Cost  │  │
│  │  (stacked area)                  │ │  (horizontal bar)        │  │
│  └──────────────────────────────────┘ └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Data sources:**
- 5 KPI cards ← `vw_kpi_summary` + measures from `dax_measures.md`
- Daily line ← `vw_daily_cost[full_date]` × `[Total Cost]`
- Provider donut ← `vw_cost_by_provider`
- Monthly stacked ← `vw_provider_monthly`
- Top services ← `vw_cost_by_service` (Top N = 5)

---

## Page 2 — Cost Analysis

**Purpose:** Drill-down tool for FinOps analysts.

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Cost Analysis                                                       │
│  [Date Range] [Provider] [Team] [Environment] [Service] [Region]    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Cost Over Time (line + area, filtered)                       │  │
│  │  Source: vw_daily_cost                                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────┬────────────────────────────────┤
│  Cost by Service (treemap)         │  Cost by Team (bar)            │
│  vw_cost_by_service                │  vw_cost_by_team               │
├────────────────────────────────────┼────────────────────────────────┤
│  Cost by Region (map or bar)       │  Cost by Account (matrix)      │
│  vw_cost_by_region                 │  vw_cost_by_account            │
└────────────────────────────────────┴────────────────────────────────┘
```

**Slicers (all from vw_cost_detail):**
- `full_date` — between date picker
- `provider_name` — dropdown
- `team_name` — dropdown
- `environment_name` — dropdown
- `service_name` — dropdown
- `region_code` — dropdown

---

## Page 3 — Service Analysis

**Purpose:** Deep dive on services — which services drive cost.

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Service Analysis                                                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Service Cost Trend — multi-line (top 5 services)             │  │
│  │  Source: vw_service_monthly                                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────┬────────────────────────────────┤
│  Cost by Service Category (donut)  │  Top 10 Services (bar)         │
│  vw_cost_by_service                │  vw_cost_by_service (Top 10)   │
├────────────────────────────────────┴────────────────────────────────┤
│  Service Detail Table (matrix)                                       │
│  Columns: service_name | category | total_cost | avg | records      │
│  Sort: total_cost DESC                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Page 4 — Team / Department Analysis

**Purpose:** Showback/chargeback — who spends what.

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Team Analysis                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Monthly Cost by Team (stacked bar)                           │  │
│  │  Source: vw_team_monthly                                      │  │
│  └───────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────┬────────────────────────────────┤
│  Team Share (donut)                │  Environment Split (donut)     │
│  vw_cost_by_team                   │  vw_cost_by_environment        │
├────────────────────────────────────┴────────────────────────────────┤
│  Team KPI Table:                                                     │
│  team_name | total_cost | pct_of_total | records                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Optional:** Add a "chargeback" card that shows each team's cost as if
invoiced monthly — a good talking point for a portfolio demo.

---

## Page 5 — Anomaly Analysis

**Purpose:** Show detected cost anomalies. Populated after Phase 6.

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Anomaly Analysis                                                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                    │
│  │ Total   │ │ Critical│ │ High    │ │ Impact  │                    │
│  │Anomalies│ │         │ │         │ │   $     │                    │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Actual vs Expected Cost Over Time (dual-line)                │  │
│  │  Source: vw_anomalies                                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  Anomaly Table (detail):                                             │
│  anomaly_date | service | resource | expected | actual | severity   │
│  Conditional formatting on severity (red/orange/yellow)             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Page 6 — Forecast

**Purpose:** Future spend projection. Populated after Phase 7.

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Forecast                                                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Historical Cost + Forecast + Confidence Band                 │  │
│  │  Source: vw_daily_cost (actual) + vw_forecasts (predicted)    │  │
│  │  Shaded area: [Forecast Lower Bound] to [Forecast Upper Bound]│  │
│  └───────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────┬────────────────────────────────┤
│  Next 7 Days Forecast (cards)      │  Next 30 Days Forecast (line)  │
│  vw_forecasts WHERE period = '7d'  │  vw_forecasts WHERE period='30d'│
├────────────────────────────────────┴────────────────────────────────┤
│  Forecast vs Actual (matrix):                                        │
│  month | actual | forecast | variance | variance %                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Page 7 — Optimization

**Purpose:** Show savings opportunities. Populated after Phase 8.

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Optimization                                                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Potential   │  │     High     │  │   Medium     │               │
│  │  Monthly $   │  │   Priority   │  │   Priority   │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Savings by Category (bar)                                    │  │
│  │  Source: vw_optimization_savings                              │  │
│  └───────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  Recommendations Table:                                              │
│  resource | category | finding | saving | priority | status         │
│  Slicers: priority, status                                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Formatting conventions

| Element | Style |
|---|---|
| Background | `#F5F5F5` (light grey) |
| Cards | White with 2 px border `#E0E0E0` |
| Headings | Font 18, bold, color `#333333` |
| Accent (positive) | `#107C10` (green) |
| Accent (warning) | `#FF8C00` (orange) |
| Accent (critical) | `#D13438` (red) |
| Trend lines | `#0078D4` (Microsoft blue) |
| Fonts | Segoe UI (default) |

Power BI theme JSON is optional but improves consistency. Once all pages are
built, you can export the theme via **View → Themes → Save current theme**.