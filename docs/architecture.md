# CloudFinOps — Architecture

> **Phase 1 status**: project scaffolding + synthetic data generation.
> Later phases extend this document as each layer is built.

## High-Level Data Flow

```mermaid
flowchart TD
    A[CSV / Excel / Cloud Billing Export] --> B[Python ETL Pipeline]
    B --> C[Raw Data Layer - staging tables]
    C --> D[Transformation Layer - clean / validate / enrich]
    D --> E[(Relational Database - MySQL)]
    E --> F[SQL Analytics Views]
    E --> G[Python ML Modules]
    F --> H[Power BI Reports]
    G --> H
    E --> I[Java Spring Boot REST API]
    I --> J[React Dashboard]
    I --> H