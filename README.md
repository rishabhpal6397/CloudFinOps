# CloudFinOps — Cloud Cost Intelligence & Optimization Platform

> An end-to-end multi-cloud FinOps platform for ingesting, validating, transforming, analyzing, forecasting, and optimizing cloud spending across AWS, Microsoft Azure, and Google Cloud Platform.

## 📌 Overview

**CloudFinOps** is a portfolio-grade cloud cost intelligence platform designed to demonstrate practical engineering across:

- Data Engineering
- Python
- Pandas / NumPy
- SQL / MySQL
- Machine Learning
- Java / Spring Boot
- React
- Power BI
- Cloud billing data integration
- Data quality, testing, logging, and observability

The platform converts provider-specific billing data into a common analytical model, processes it through an ETL pipeline, stores it for analytics, and exposes insights such as cost trends, anomalies, forecasts, and optimization opportunities.

The project starts with synthetic billing data and is designed to support real cloud billing exports later.

---

## 🎯 Problem Statement

Cloud billing data differs between providers and becomes difficult to analyze consistently across:

- Cloud providers
- Accounts / subscriptions / projects
- Services
- Regions
- Resources
- Teams
- Environments

CloudFinOps addresses this by creating a **provider-neutral cost intelligence layer** capable of answering questions such as:

- How much are we spending?
- Which provider is costing the most?
- Which services are driving spending?
- Which teams and environments are responsible for the cost?
- Which resources show unusual behavior?
- What will future spending look like?
- Where are potential cost-saving opportunities?

---

## 🏗️ System Architecture

```text
 ┌──────────────────────────────────────────────────────────────┐
 │                     BILLING SOURCES                         │
 │                                                              │
 │   CSV / Excel     AWS CUR     Azure Export     GCP Export    │
 └──────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                    PYTHON INGESTION                          │
 │              Provider-specific adapters                      │
 └──────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                 VALIDATION & DATA QUALITY                    │
 │       Schema • Nulls • Dates • Cost • Usage • Currency       │
 └──────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                       CLEANING                               │
 │          Type conversion • Duplicates • Invalid rows         │
 └──────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                    TRANSFORMATION                            │
 │       Time dimensions • Keys • Metrics • Categories           │
 └──────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                         MySQL                                │
 │                  Analytical data store                        │
 └───────────────┬──────────────────────┬───────────────────────┘
                 │                      │
                 ▼                      ▼
       ┌──────────────────┐    ┌─────────────────────┐
       │ SQL / Analytics  │    │ Python ML & Rules   │
       └────────┬─────────┘    └──────────┬──────────┘
                │                         │
                └────────────┬────────────┘
                             ▼
                  ┌──────────────────────┐
                  │   Spring Boot API    │
                  └──────────┬───────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
             ┌──────────────┐  ┌──────────────┐
             │ React        │  │ Power BI     │
             │ Dashboard    │  │ Reporting    │
             └──────────────┘  └──────────────┘
```

---

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Data Generation | Python, Faker, NumPy, Pandas |
| Data Ingestion | Python |
| Data Validation | Python, Pandas |
| Data Cleaning | Python, Pandas |
| Transformation | Python, Pandas, NumPy |
| Database | MySQL |
| Analytics | SQL, Pandas |
| Machine Learning | Python |
| Forecasting | Python time-series models |
| Optimization | Python rule-based engine |
| Backend | Java, Spring Boot |
| Frontend | React, JavaScript |
| Reporting | Microsoft Power BI |
| Testing | pytest / unittest |
| Version Control | Git / GitHub |

---

# 📊 Current Dataset

The current synthetic development dataset contains:

| Metric | Value |
|---|---:|
| Billing records | 40,950 |
| Unique resources | 150 |
| Date range | 2026-01-01 → 2026-09-30 |
| Cloud providers | AWS, Azure, GCP |
| Records per provider | 13,650 |
| Accounts | 6 |
| Services | 15 |
| Regions | 9 |
| Teams | 6 |
| Environments | 4 |
| Total synthetic cost | $3,534,435.01 |
| Raw columns | 13 |
| Transformed columns | 26 |

The dataset is synthetic and is intended for development, testing, demonstrations, and portfolio purposes.

---

# 🔄 Data Engineering

CloudFinOps follows:

```text
Extract
   ↓
Validate
   ↓
Clean
   ↓
Transform
   ↓
Load
   ↓
Analyze
```

## 1. Ingestion

The ingestion layer supports the canonical billing input model and is designed to accept:

- CSV
- Excel
- Provider-specific billing exports

The provider-specific integrations are isolated from downstream processing.

---

## 2. Validation

The validation layer checks:

- Required columns
- Empty datasets
- Missing required values
- Invalid billing dates
- Negative costs
- Negative usage
- Missing resource IDs
- Currency validity
- Overall data quality

The project also contains deliberately corrupted test data to verify that invalid records are detected.

---

## 3. Cleaning

The cleaning layer performs:

- Text normalization
- Data-type conversion
- Duplicate detection and removal
- Invalid-record identification
- Cleaning statistics generation

Current normal-data baseline:

```text
Input records       : 40,950
Duplicates removed  : 0
Invalid records     : 0
Valid records       : 40,950
Records accounted   : 40,950
```

Generated outputs include:

```text
data/cleaned_billing_data.csv
data/cleaning_report.csv
```

---

## 4. Transformation

The transformation layer enriches the canonical billing records with analytical fields.

Current derived fields include:

```text
year
month
month_name
quarter
day_of_month
day_of_week
is_weekend
cost_per_unit
provider_key
service_key
environment_key
team_key
cost_category
```

Current cost categories:

- Compute
- Storage
- Database
- Serverless
- Networking
- Other

The transformed dataset currently contains **26 columns** while preserving all **40,950** records.

---

## 5. ETL Orchestration

The ETL orchestrator executes:

```text
Extract
   ↓
Validate
   ↓
Clean
   ↓
Transform
```

The pipeline records:

- Records read
- Duplicates removed
- Invalid records
- Valid records
- Transformed records
- Execution time
- Final status

Example successful run:

```text
Records read        : 40,950
Duplicates removed  : 0
Invalid records     : 0
Valid records       : 40,950
Transformed records : 40,950
Status              : SUCCESS
```

Pipeline logging is written to:

```text
logs/billing_etl.log
```

---

# 🗃️ Canonical Billing Model

CloudFinOps uses a provider-neutral billing schema.

| Column | Description |
|---|---|
| `billing_date` | Billing / usage date |
| `provider` | AWS / Azure / GCP |
| `account_id` | Account, subscription, or project identifier |
| `service` | Cloud service |
| `region` | Cloud region |
| `resource_id` | Provider resource identifier |
| `resource_name` | Resource name |
| `team` | Owning team |
| `environment` | Environment such as dev/test/prod |
| `usage_quantity` | Usage amount |
| `usage_unit` | Usage unit |
| `cost` | Cost amount |
| `currency` | Currency code |

The purpose of this model is to keep downstream analytics independent of provider-specific billing schemas.

---

# ☁️ Multi-Cloud Support

## AWS

Real AWS billing integration is planned around **AWS Cost and Usage Reports (CUR)**.

Target mappings include:

```text
CloudFinOps field  →  AWS CUR field

billing_date       →  line_item_usage_start_date
provider           →  AWS
account_id         →  line_item_usage_account_id
service            →  product_product_name / product code
region             →  product_region_code
resource_id        →  line_item_resource_id
usage_quantity     →  line_item_usage_amount
usage_unit         →  pricing / usage unit
cost               →  line_item_unblended_cost
currency           →  line_item_currency_code
```

AWS cost-allocation tags can be used for team and environment enrichment when available.

## Microsoft Azure

Planned integration with Azure Cost Management exports.

## Google Cloud Platform

Planned integration with GCP Billing Export.

The downstream data model remains provider-neutral.

---

# 📈 Analytics

The analytics layer is intended to provide:

### Cost Overview

- Total cloud spend
- Daily/monthly spend
- Spend changes
- Provider distribution
- Service contribution

### Cost Breakdown

Analysis by:

- Provider
- Account
- Service
- Region
- Resource
- Team
- Environment
- Cost category

### Trend Analysis

Historical spending can be analyzed to identify:

- Increasing costs
- Decreasing costs
- Recurring patterns
- Service-level trends
- Team/environment trends

---

# 🤖 Machine Learning

CloudFinOps includes a dedicated ML layer for advanced cost intelligence.

## 🔎 Anomaly Detection

The anomaly pipeline is designed to identify unusual spending behavior.

Anomaly records can contain:

```text
expected_cost
actual_cost
deviation
anomaly_score
resource/service context
```

The objective is to identify abnormal cloud spending while preserving enough context for investigation.

---

## 📊 Forecasting

The forecasting pipeline works with historical cost time series and evaluates models using backtesting.

Evaluation metrics include:

- MAE — Mean Absolute Error
- RMSE — Root Mean Squared Error
- MAPE — Mean Absolute Percentage Error, where applicable

Forecast outputs include:

```text
forecast_date
generated_on
forecast_period
service_key
predicted_cost
lower_bound
upper_bound
model_name
```

Services without sufficient historical data are skipped explicitly instead of producing unreliable forecasts.

---

# 💰 Optimization Engine

CloudFinOps contains an explainable, rule-based optimization engine.

Current rules:

| Rule | Purpose |
|---|---|
| Recent Cost Collapse | Detect resources whose recent spending has significantly fallen |
| Near-Zero Cost | Identify resources with negligible spending |
| Oversized by Unit Cost | Compare resource cost-per-unit against service-level median |
| Storage Growth | Detect sustained storage-cost growth |
| Database Spike | Detect database spending spikes against historical baseline |

Each recommendation can contain:

```text
resource_key
resource_id
resource_name
category
finding
estimated_monthly_saving
priority
```

## Recommendation Priority

| Estimated Monthly Saving | Priority |
|---:|---|
| ≥ $1,000 | HIGH |
| $200 – < $1,000 | MEDIUM |
| < $200 | LOW |

The recommendations are **advisory**. The platform does not automatically terminate, resize, stop, or delete cloud resources.

---

# 🧪 Testing & Quality

Testing is integrated into the development workflow.

Current ETL testing covers:

- Schema validation
- Invalid data detection
- Cleaning behavior
- Transformation behavior
- Record-count preservation
- Date validation
- Cost metric validation
- Category validation
- Normalized-key validation
- End-to-end ETL execution

Current baseline:

```text
Automated ETL tests: 9 passing
```

The invalid-data tests intentionally inject bad records. Seeing invalid data reported during that test is expected; the test succeeds when the validation layer correctly detects it.

Typical test commands:

```bash
pytest -v
```

Forecasting tests:

```bash
pytest ml/tests/test_forecasting.py -v
```

---

# 📁 Project Structure

The repository is organized by responsibility.

```text
CloudFinOps/
│
├── data/
│   ├── raw_billing_data.csv
│   ├── raw_billing_data.xlsx
│   ├── test_invalid_billing_data.csv
│   ├── cleaned_billing_data.csv
│   ├── cleaning_report.csv
│   └── transformed_billing_data.csv
│
├── data-engineering/
│   ├── generators/
│   │   └── generate_billing_data.py
│   ├── ingestion/
│   ├── validation/
│   ├── cleaning/
│   ├── transformation/
│   ├── etl/
│   ├── pipeline/
│   ├── tests/
│   └── utils/
│
├── ml/
│   ├── common.py
│   ├── forecasting/
│   ├── optimization/
│   └── tests/
│
├── backend/
│   └── Spring Boot application
│
├── frontend/
│   └── React application
│
├── powerbi/
│   └── Power BI assets
│
├── logs/
│   └── billing_etl.log
│
├── requirements.txt
└── README.md
```

Some directories are introduced as their corresponding implementation phases are completed.

---

# ⚙️ Getting Started

## Prerequisites

Install:

- Python 3.x
- MySQL
- Java JDK
- Maven
- Node.js and npm
- Git
- Power BI Desktop

---

## 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/CloudFinOps.git
cd CloudFinOps
```

Replace `<your-username>` with the actual GitHub username/repository URL.

---

## 2. Create Python Virtual Environment

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Generate Synthetic Billing Data

```bash
python data-engineering/generators/generate_billing_data.py
```

This produces:

```text
data/raw_billing_data.csv
data/raw_billing_data.xlsx
```

---

## 5. Run the ETL Pipeline

```bash
python data-engineering/pipeline/run_billing_etl.py
```

Expected flow:

```text
Extract       ✓
Validate      ✓
Clean         ✓
Transform     ✓
              ─────
SUCCESS
```

---

## 6. Run Tests

```bash
pytest -v
```

---

# 🛢️ MySQL

Create the project database:

```sql
CREATE DATABASE cloudfinops;
```

Use environment variables for credentials:

```text
DB_HOST=localhost
DB_PORT=3306
DB_NAME=cloudfinops
DB_USER=<username>
DB_PASSWORD=<password>
```

Never commit actual credentials to GitHub.

Recommended `.env.example`:

```text
DB_HOST=localhost
DB_PORT=3306
DB_NAME=cloudfinops
DB_USER=
DB_PASSWORD=
```

---

# 🔐 Security

CloudFinOps follows these principles:

- No credentials committed to source control
- Database credentials supplied through environment variables
- Cloud credentials kept outside source code
- Secrets excluded from logs
- Input validation before processing
- Authentication/authorization planned for multi-user deployment
- `.env` excluded from Git
- `.env.example` used for configuration documentation

Example `.gitignore` entries:

```gitignore
.venv/
.env
__pycache__/
*.pyc
logs/*.log
```

---

# 🖥️ React Dashboard

The planned React dashboard provides an interactive interface for cloud cost intelligence.

## Executive Overview

- Total cloud spend
- Spend change
- Provider distribution
- Major cost drivers
- Potential savings

## Cost Analysis

Filters:

```text
Date
Provider
Account
Service
Region
Team
Environment
Category
```

## Anomaly Analysis

- Anomaly count
- Impacted resources
- Expected vs actual cost
- Deviation
- Anomaly score

## Forecasting

- Historical spending
- Forecasted spending
- Lower/upper bounds
- Model used
- Forecast horizon

## Optimization

- Recommendation category
- Resource
- Finding
- Estimated monthly savings
- Priority

---

# 📊 Power BI

Power BI provides the business reporting layer.

Planned reports include:

- Executive cloud cost overview
- Daily/monthly cost trends
- Provider comparison
- Service contribution
- Team spending
- Environment spending
- Top resources
- Anomaly impact
- Forecast vs actual
- Optimization opportunities

The reporting model should use consistent business definitions with the ETL and backend layers.

---

# 🔌 Spring Boot Backend

The planned backend provides a REST API between the analytical layer and presentation applications.

Responsibilities include:

- API endpoints
- Request validation
- DTOs
- Service layer
- Repository layer
- Database access
- Error handling
- Authentication/authorization
- Serving analytics, ML, and optimization results

Target flow:

```text
React / Power BI
       ↓
Spring Boot REST API
       ↓
MySQL
       ↓
Processed Billing + ML + Recommendations
```

---

# 🛣️ Development Roadmap

## Phase 1 — Data Generation

- [x] Synthetic billing generator
- [x] AWS/Azure/GCP representation
- [x] Resource-level data
- [x] Controlled cost variation
- [x] Synthetic anomalies

## Phase 2 — Data Engineering

- [x] Ingestion
- [x] Schema validation
- [x] Data-quality validation
- [x] Cleaning
- [x] Transformation
- [x] ETL orchestration
- [x] Logging
- [x] Automated tests

## Phase 3 — Database

- [ ] MySQL schema
- [ ] Dimension tables
- [ ] Fact billing table
- [ ] Indexing
- [ ] Analytical SQL
- [ ] Data reconciliation

## Phase 4 — Analytics

- [ ] Cost analytics
- [ ] Provider comparison
- [ ] Service analysis
- [ ] Team/environment analysis
- [ ] Resource analytics

## Phase 5 — Machine Learning

- [ ] Anomaly detection integration
- [ ] Forecasting integration
- [ ] Backtesting
- [ ] Model comparison
- [ ] Forecast persistence

## Phase 6 — Optimization

- [x] Optimization rule framework
- [x] Recent cost collapse
- [x] Near-zero cost
- [x] Oversized resources
- [x] Storage growth
- [x] Database spike detection
- [ ] Full database integration

## Phase 7 — Backend

- [ ] Spring Boot project
- [ ] REST APIs
- [ ] DTOs
- [ ] Service layer
- [ ] Repository layer
- [ ] API validation
- [ ] Error handling
- [ ] Authentication / authorization

## Phase 8 — Frontend

- [ ] React application
- [ ] Dashboard
- [ ] Filters
- [ ] Charts
- [ ] Anomaly view
- [ ] Forecast view
- [ ] Optimization view

## Phase 9 — Power BI

- [ ] Data model
- [ ] Measures
- [ ] Executive dashboard
- [ ] Cost analysis
- [ ] Forecasting
- [ ] Optimization report

## Phase 10 — Real Cloud Billing

- [ ] AWS CUR adapter
- [ ] Azure Cost Management adapter
- [ ] GCP Billing Export adapter
- [ ] Provider reconciliation
- [ ] Production-oriented ingestion

---

# 🧠 Engineering Principles

### 1. Validate before transforming

Bad data should be identified before it enters downstream analytics.

### 2. Isolate provider-specific logic

Provider adapters should translate external billing schemas into the common CloudFinOps model.

### 3. Make recommendations explainable

Every optimization recommendation should explain **why** a resource was flagged.

### 4. Preserve data lineage

```text
Source
  ↓
Raw Data
  ↓
Cleaned Data
  ↓
Transformed Data
  ↓
Database
  ↓
Analytics / ML
  ↓
Recommendation
  ↓
Dashboard / Report
```

### 5. Fail visibly

A pipeline that silently produces incorrect results is worse than one that fails clearly.

### 6. Test before declaring completion

A development phase is considered complete only after its acceptance criteria and validation tests pass.

---

# 📋 Project Documentation

A detailed Software Requirements Specification is maintained for the project.

The SRS covers:

- Product overview
- Scope
- Stakeholders
- Functional requirements
- Data requirements
- ETL requirements
- Analytics requirements
- ML requirements
- Optimization requirements
- Backend API requirements
- React dashboard requirements
- Power BI requirements
- Security
- Non-functional requirements
- Testing
- Deployment
- Acceptance criteria
- Future enhancements

File:

```text
CloudFinOps_SRS.docx
```

---

# 🚀 Future Vision

The long-term goal is to evolve CloudFinOps into a realistic multi-cloud FinOps intelligence platform:

```text
Real Cloud Billing
       ↓
Automated Ingestion
       ↓
Unified Cost Model
       ↓
Data Quality
       ↓
Historical Analytics
       ↓
Anomaly Detection
       ↓
Cost Forecasting
       ↓
Optimization Recommendations
       ↓
Spring Boot API
       ↓
React Dashboard
       ↓
Power BI Reporting
```

Potential future capabilities:

- Scheduled ingestion
- Multi-currency support
- Budget monitoring
- Cost alerts
- Tag-quality monitoring
- Showback / chargeback
- Advanced forecasting
- Provider-specific rightsizing
- Recommendation lifecycle management
- Docker/container deployment
- CI/CD
- Authentication and RBAC
- Multi-tenant architecture

---

# ⚠️ Disclaimer

CloudFinOps is a learning and portfolio project.

The initial billing dataset is synthetic and does not represent actual cloud charges.

Optimization recommendations are analytical suggestions and should be reviewed by an engineer or FinOps professional before taking action on real cloud resources.

---

# 👨‍💻 Author

**Rishabh Pal**

B.Tech — Computer Science & Engineering

Areas of interest:

- Data Engineering
- Cloud Computing
- Machine Learning
- Python
- SQL
- Java
- React
- FinOps

---

# ⭐ Project Status

**Status: 🚧 Active Development**

The Python data-engineering foundation is established, including synthetic billing generation, ingestion, validation, cleaning, transformation, ETL orchestration, logging, testing, and the optimization-rule framework.

Database integration, advanced analytics, ML integration, backend, frontend, Power BI, and real cloud billing adapters are being developed incrementally.
