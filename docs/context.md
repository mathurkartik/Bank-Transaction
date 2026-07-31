# System Context & Architecture Guide: Aura Bank Financial Analytics

This document serves as the primary system context reference for developers, data engineers, and AI assistants working on the **Aura Bank Financial Analytics** data platform.

---

## 🎯 1. Overview & System Mission

**Aura Bank Financial Analytics** is an end-to-end modern Data Lakehouse and Analytics platform built to process over **1.75+ million bank transaction records** and customer profiles. The system ingests raw banking operations data, processes it through multi-tier Spark Lakehouse layers (Bronze/Raw ➔ Silver ➔ Gold), populates a PostgreSQL Data Warehouse, and exposes real-time executive KPIs and interactive dashboards.

### Core Capabilities
* **Ingestion & Data Cleaning**: Transforms raw Kaggle bank transactions dataset (`bank_transactions.csv`), generating enriched synthetic records for multi-branch operations, loans, revenues, and branch costs.
* **Lakehouse ETL Pipeline**: PySpark vectorized batch jobs transforming raw data into partitioned Snappy-compressed Parquet datasets across Silver and Gold layers.
* **Data Warehousing**: PostgreSQL schemas (`bank_dwh`) with analytical views (`vw_customer_profitability`, `vw_branch_performance`, `vw_loan_portfolio`).
* **Workflow Orchestration**: Apache Airflow DAG (`financial_analytics_pipeline`) coordinating data integration, PySpark jobs, and data integrity verification.
* **Interactive Visualization**: Streamlit dark-mode analytics dashboard using Plotly for branch performance, customer segment profitability, and credit risk metrics.

---

## 📂 2. Repository Structure

```
M5/
├── .gitignore                      # Git exclusion rules for environments, logs, and datasets
├── Dockerfile.airflow              # Custom Docker image for Airflow with PySpark dependencies
├── README.md                       # High-level project documentation
├── docker-compose.yml              # Multi-container orchestration (Airflow, PostgreSQL, Spark)
├── kaggle original 1.txt           # Raw transaction sample metadata / reference format
├── requirements.txt                # Python package dependencies
│
├── airflow/
│   └── dags/
│       └── financial_analytics_pipeline.py  # Airflow DAG managing full pipeline lifecycle
│
├── docs/
│   ├── context.md                  # System context and architectural guide (this document)
│   └── project_details.md          # In-depth architectural details, schemas, and analytical directions
│
├── scripts/
│   ├── integrate_kaggle_synthetic.py  # Cleans raw Kaggle data & generates synthetic banking entities
│   ├── setup_directories.sh           # Directory initialization script for Lakehouse structure
│   └── verify_data_integrity.py       # Data sanity and record count verification script
│
├── spark_jobs/
│   ├── config/
│   │   └── spark_config.py          # PySpark session configuration and Lakehouse path constants
│   └── batch/
│       ├── bronze_to_silver.py      # Cleans, type-casts, and enriches raw datasets into Silver Parquet
│       └── silver_to_gold.py        # Aggregates Silver datasets into Gold KPIs & loads PostgreSQL
│
├── sql_warehouse/
│   ├── 01_init_schema.sql           # DDL for PostgreSQL warehouse tables & indexes
│   └── 02_financial_kpi_views.sql   # DDL for analytical views & business rules
│
└── streamlit_app/
    └── dashboard.py                 # Streamlit & Plotly executive analytics web application
```

---

## 🏗️ 3. End-to-End Data Pipeline Architecture

```
┌────────────────────────────────────────────────────────┐
│ 1. Raw Ingestion & Synthetic Data Integration          │
│    scripts/integrate_kaggle_synthetic.py               │
│    (Kaggle CSV ➔ 1.7M+ Transactions, 884k Customers)   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 2. Bronze / Processed Layer (CSV)                      │
│    data/processed/{customers,transactions,costs,...}   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 3. Silver Layer PySpark ETL                            │
│    spark_jobs/batch/bronze_to_silver.py                │
│    - Schema enforcement, age/income/balance segmenting │
│    - Format: Snappy Parquet (data/silver/)             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 4. Gold Layer & Warehouse Load                         │
│    spark_jobs/batch/silver_to_gold.py                  │
│    - Aggregates Customer Profitability, Branch CIR,    │
│      and Loan Risk Exposure                           │
│    - Writes to data/gold/ & PostgreSQL (bank_dwh)      │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 5. Analytics & Visualization                           │
│    sql_warehouse/ (PostgreSQL Analytical Views)        │
│    streamlit_app/dashboard.py (Streamlit + Plotly App) │
└────────────────────────────────────────────────────────┘
```

---

## ⚙️ 4. Tech Stack & Dependencies

* **Language**: Python 3.10+
* **Data Processing**: Apache PySpark 3.5.x, Pandas 2.x
* **Database & Storage**: PostgreSQL 13, Apache Parquet (Snappy Compression)
* **Orchestration**: Apache Airflow 2.8.x
* **Frontend / UI**: Streamlit, Plotly Express
* **Infrastructure**: Docker, Docker Compose

---

## 🚀 5. Getting Started & Operations

### Local Environment Execution

1. **Environment Setup**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. **Data Integration**:
   ```bash
   python scripts/integrate_kaggle_synthetic.py
   ```

3. **Run Spark ETL Jobs**:
   ```bash
   python spark_jobs/batch/bronze_to_silver.py
   python spark_jobs/batch/silver_to_gold.py
   ```

4. **Verify Data Integrity**:
   ```bash
   python scripts/verify_data_integrity.py
   ```

5. **Launch Analytics Dashboard**:
   ```bash
   streamlit run streamlit_app/dashboard.py
   ```

---

## 📌 6. Key Metrics & Business Definitions

* **Cost-Income Ratio (CIR)**: `Total Branch Costs / Gross Revenue` (Target: < 50% = Excellent).
* **Customer Net Profit**: `Total Revenue - Processing Costs` (₹5 fixed per transaction).
* **Loan Portfolio Utilization**: `Outstanding Principal / Total Loan Portfolio Disbursed`.
