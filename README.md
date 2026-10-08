# CloudFinOps — Cloud Cost Intelligence & Optimization Platform

An end-to-end FinOps platform that ingests cloud billing data, transforms it into a star-schema warehouse, detects cost anomalies, forecasts future spend, and surfaces actionable optimization recommendations through a REST API and Power BI.

> **Portfolio project.** All data is synthetic. No real cloud credentials required.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Java](https://img.shields.io/badge/Java-17-007396?logo=openjdk&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.3-6DB33F?logo=springboot&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?logo=scikitlearn&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Desktop-F2C811?logo=powerbi&logoColor=black)

---

## What It Does

```
CSV / Excel billing export
        │
        ▼
   Python ETL  →  MySQL star schema  →  SQL analytics views
                                            │
                     ┌──────────────────────┼──────────────────────┐
                     ▼                      ▼                      ▼
              Anomaly Detection       Forecasting          Optimization
              (z-score + IF)          (LR + RF)            (5 rule engines)
                     │                      │                      │
                     └──────────────────────┼──────────────────────┘
                                            ▼
                                   Spring Boot REST API
                                            │
                                ┌───────────┴───────────┐
                                ▼                       ▼
                          React Dashboard          Power BI
```

---

## Features

| Module | What It Does |
|---|---|
| **Synthetic Generator** | 12 months × 120K records across AWS/Azure/GCP, with injected trends, seasonality, spikes, and sustained anomalies |
| **ETL Pipeline** | Extract → Validate → Clean → Transform → Enrich → Load with full validation reporting |
| **Star Schema** | 9 dimensions + 1 fact table (119K rows) + 4 FinOps tables |
| **Analytics Views** | 20 SQL views optimized for BI consumption |
| **Anomaly Detection** | Rolling z-score + Isolation Forest → 250+ anomalies with severity tiers |
| **Forecasting** | Linear Regression + Random Forest → 7-day and 30-day horizons with confidence bands |
| **Optimization** | 5 rule engines → 35+ recommendations, $144K/month identified savings |
| **REST API** | Spring Boot 3 with DTOs, exception handling, CORS |
| **Power BI** | 7 pre-designed report pages with DAX measures and CSV export pipeline |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data Engineering | Python 3.12 · Pandas · NumPy · Faker |
| Database | MySQL 8 (star schema + 20 views) |
| Machine Learning | scikit-learn (IsolationForest, LinearRegression, RandomForest) |
| Backend | Java 17 · Spring Boot 3.3 · Maven |
| Frontend | React 18 · Vite · Axios · React Router |
| BI | Power BI Desktop |

---

## Quick Start

### Prerequisites

- GitHub Codespace (recommended) **or** local machine with Python 3.12+, MySQL 8, Java 17, Node 20

### Run in a GitHub Codespace

```bash
# 1. Start MySQL (if not already running)
sudo service mysql start

# 2. Generate synthetic billing data (~30s)
python data-engineering/generators/generate_billing_data.py

# 3. Apply schema + views
python data-engineering/apply_schema.py
python data-engineering/apply_views.py

# 4. Run ETL and load into MySQL (~30s)
python data-engineering/run_etl.py \
  --input data/raw/synthetic_billing_data.csv \
  --output data/processed \
  --reports data/reports \
  --load-db

# 5. Run ML modules
python ml/run_anomaly_detection.py     # ~10s
python ml/run_forecasting.py           # ~30s
python ml/run_optimization.py          # ~10s

# 6. Export for Power BI
python data-engineering/export_for_powerbi.py

# 7. Start the REST API
cd backend/cloudfinops-api && mvn spring-boot:run
```

API is now live at `http://localhost:8080/api`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health check |
| `GET` | `/api/dashboard/summary` | KPI snapshot (total cost, MoM change, records) |
| `GET` | `/api/costs/daily` | Daily cost trend (365 rows) |
| `GET` | `/api/costs/monthly` | Monthly totals with MoM deltas |
| `GET` | `/api/costs/by-provider` | AWS / Azure / GCP breakdown |
| `GET` | `/api/costs/by-service` | Cost by service with category |
| `GET` | `/api/costs/by-team` | Cost per team + % of total |
| `GET` | `/api/costs/by-environment` | Production / staging / dev split |
| `GET` | `/api/costs/by-region` | Regional spend |
| `GET` | `/api/costs/by-account` | Per-account totals |

*(Phases 9b–11 add `/api/anomalies`, `/api/forecasts`, `/api/recommendations`, `/api/budgets`.)*

---

## Project Structure

```
CloudFinOps/
├── backend/cloudfinops-api/        # Spring Boot REST API
├── frontend/cloudfinops-dashboard/ # React dashboard (Phase 10)
├── data-engineering/
│   ├── generators/                 # Synthetic billing generator
│   ├── etl/                        # ETL pipeline modules
│   ├── validation/                 # Report writers
│   └── tests/                      # Pytest suite
├── database/
│   ├── schema/                     # DDL (dimensions, facts, FinOps tables)
│   └── views/                      # 20 reporting views
├── ml/
│   ├── anomaly_detection/          # z-score + Isolation Forest
│   ├── forecasting/                # LR + Random Forest
│   └── optimization/               # 5 rule engines
├── powerbi/documentation/          # DAX measures, page designs, setup
├── docs/                           # Architecture, DB design, FinOps concepts
└── README.md
```

---

## Data Model Highlights

- **Star schema** — `fact_cost` (119,463 rows) surrounded by 9 dimension tables
- **Grain** — one row per resource per day per service
- **Surrogate keys** — `INT AUTO_INCREMENT` on every dimension
- **Date dimension** — pre-populated 2024–2027 (1,461 days)
- **20 reporting views** — trends, dimension rollups, KPI summary, drill-through

---

## Example Results

```
Total spend (12 months)     : $26.5M
Records loaded              : 119,463
Providers                   : 3 (AWS, Azure, GCP)
Services tracked            : 30
Unique resources            : 553

Anomalies detected          : 253 (z-score: 13, IsolationForest: 240)
Forecasts generated         : 2,294 rows across 2 models
Optimization opportunities  : 35 recommendations
Identified monthly savings  : $144,169
```

---

## Testing

```bash
# Python (ETL + ML)
python -m pytest data-engineering/tests ml/tests -v

# Java
cd backend/cloudfinops-api && mvn test
```

---

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system design and component responsibilities
- [`docs/database-design.md`](docs/database-design.md) — star schema reference
- [`docs/finops-concepts.md`](docs/finops-concepts.md) — FinOps principles applied in this project
- [`powerbi/documentation/`](powerbi/documentation/) — DAX measures, page layouts, connection guide

---

## Roadmap

- [x] **Phase 1** — Synthetic billing data generator
- [x] **Phase 2** — Python ETL pipeline
- [x] **Phase 3** — MySQL star schema + loader
- [x] **Phase 4** — SQL analytics views
- [x] **Phase 5** — Power BI integration
- [x] **Phase 6** — Anomaly detection (statistical + ML)
- [x] **Phase 7** — Cost forecasting (LR + RF)
- [x] **Phase 8** — Optimization recommendation engine
- [x] **Phase 9** — Spring Boot REST API
- [ ] **Phase 10** — React dashboard
- [ ] **Phase 11** — Budgets, alerts, authentication
- [ ] **Phase 12** — Testing, docs, final integration

---

## License

MIT — portfolio project.

---

## Author

**Rishabh Pal** · [@rishabhpal6397](https://github.com/rishabhpal6397)
