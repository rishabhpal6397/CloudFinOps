
---

## File 9 — `README.md`

```markdown
# CloudFinOps — Cloud Cost Intelligence & Optimization Platform

An end-to-end FinOps platform that ingests cloud billing data, transforms it,
stores it in a star schema, detects anomalies, forecasts spend, and surfaces
everything through a React dashboard and Power BI reports.

> **Portfolio project.** All data is synthetic. No real cloud credentials required.

## Stack

| Layer | Technology |
|---|---|
| Data engineering | Python 3.12 · Pandas · NumPy |
| Database | MySQL 8 |
| ML | scikit-learn · statsmodels |
| Backend | Java 17 · Spring Boot 3 · Maven |
| Frontend | React 18 · Vite · JavaScript |
| BI | Power BI Desktop |

## Running in GitHub Codespaces

1. **Open the repository in a Codespace.**
   The `.devcontainer/devcontainer.json` provisions Java 17, Python 3.12, Node 20,
   installs MySQL, creates the `cloudfinops` database, and installs Python
   dependencies automatically.

2. **Wait for the bootstrap to finish.** You will see:

   ```
   CloudFinOps Codespace is ready 🚀
   MySQL    : localhost:3306
   Database : cloudfinops
   ```

3. **Generate the synthetic dataset.**

   ```bash
   python data-engineering/generators/generate_billing_data.py
   ```

   Expected output:

   ```
   ✔ Generated 120,xxx records
   ✔ Wrote data/raw/synthetic_billing_data.csv  (~35 MB)
   ```

4. **Verify the file.**

   ```bash
   head -n 5 data/raw/synthetic_billing_data.csv
   wc -l data/raw/synthetic_billing_data.csv
   ```

## Configuration

All runtime configuration is read from `.env`. The Codespace creates this file
automatically from `.env.example` on first boot. Never commit `.env`.

| Variable | Purpose |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME` | MySQL connection |
| `DB_USER`, `DB_PASSWORD` | MySQL credentials |
| `SPRING_DATASOURCE_URL` | JDBC URL for Spring Boot |
| `VITE_API_BASE_URL` | React → API base URL |
| `GEN_START_DATE`, `GEN_END_DATE` | Synthetic data date range |
| `GEN_TARGET_RECORDS` | Target record count |
| `GEN_SEED` | Reproducibility seed |

## Project Structure

```
CloudFinOps/
├── .devcontainer/          # Codespaces configuration
├── backend/                # Spring Boot (Phase 9)
├── frontend/               # React dashboard (Phase 10)
├── data-engineering/       # ETL + generators (Phases 1-2)
├── database/               # Schema + views (Phases 3-4)
├── ml/                     # Anomaly + forecast + recommend (Phases 6-8)
├── powerbi/                # BI docs (Phase 5)
└── docs/                   # Architecture + design docs
```

## Phase Progress

- [x] **Phase 1** — Setup, architecture, synthetic data generator
- [ ] Phase 2 — Python ETL pipeline
- [ ] Phase 3 — MySQL schema + loader
- [ ] Phase 4 — SQL analytics + reporting views
- [ ] Phase 5 — Power BI dashboards
- [ ] Phase 6 — Anomaly detection
- [ ] Phase 7 — Cost forecasting
- [ ] Phase 8 — Optimization recommendations
- [ ] Phase 9 — Spring Boot REST API
- [ ] Phase 10 — React dashboard
- [ ] Phase 11 — Auth, budgets, alerts
- [ ] Phase 12 — Testing, docs, integration

## License

MIT (portfolio project).