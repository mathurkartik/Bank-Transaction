# Master Architecture Enhancements & Target Blueprint: Aura Bank Financial Analytics

This document provides a comprehensive, production-grade architectural enhancement plan for the **Aura Bank Financial Analytics Data Lakehouse**, based on the business requirements and technical specifications outlined in [`docs/context file.md`](file:///c:/Users/KartikMathur/Desktop/Project/M5/docs/context%20file.md).

---

## 🎯 1. Executive Summary & Enhancement Vision

The goal of this architectural blueprint is to elevate the current batch Data Lakehouse into an enterprise-grade, **Hybrid Real-Time, Predictive, and Automated Data Engineering Platform**. 

By expanding the data model, integrating **Apache Kafka streaming**, embedding **PySpark MLlib predictive risk models**, enforcing **Great Expectations data quality gates**, and supporting **Apache Iceberg time travel & Tableau BI**, the platform transitions from basic descriptive reports into a full-stack financial engineering ecosystem.

---

## 📊 2. Architecture Comparison Matrix

| Architectural Area | Current Baseline State | Upgraded Target Architecture |
| :--- | :--- | :--- |
| **Ingestion Pattern** | Batch CSV file processing | **Hybrid**: Batch Medallion Lakehouse + Real-time **Kafka** Event Streaming |
| **Processing Engine** | PySpark Batch ETL | PySpark Batch ETL + **Spark Structured Streaming** |
| **Storage & Table Format** | Standard Parquet files | **Apache Iceberg / Parquet** (Supports time-travel, ACID, & schema evolution) |
| **Data Quality** | Manual post-execution script | **Great Expectations (GE)** in-pipeline assertions & Quarantine layer |
| **Analytics Capability** | Descriptive (KPIs, CIR, Margins) | **Predictive & Diagnostic** (Loan Default Scoring, Churn, Fraud Detection) |
| **Orchestration** | Basic Airflow DAG | Advanced Airflow DAG (File Sensors, Task Retries, Failure Alerts) |
| **Warehouse & BI** | Streamlit + PostgreSQL | Streamlit + **Tableau JDBC/ODBC Semantic Views** |

---

## 🏗️ 3. End-to-End System Target Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                  TARGET SYSTEM ARCHITECTURE BLUEPRINT                              |
|                                                                                                   |
|  [Real-Time Event Ingestion]                                                                      |
|  Python Kafka Producer ──► Kafka Topic: bank.transactions ──► Spark Structured Streaming          |
|  (Simulated live txns)     (Partitioned / Low Latency)      (Watermarking & 5-min Windows)        |
|                                                                     │                             |
|                                                                     ├──► Real-Time Stream Sink    |
|                                                                     │    (PostgreSQL / Dashboard) |
|                                                                     │                             |
|  [Batch Medallion Lakehouse]                                        ▼                             |
|  Kaggle + Synthetic ────► Bronze Layer ────────► Silver Layer (Enriched) ──► PySpark MLlib Engine |
|  (Scripts & Ingestion)    (Iceberg/Parquet)      (Great Expectations Gates)  (Loan Default Score)  |
|                                                          │                         │              |
|                                                          ▼                         ▼              |
|                                                Gold Layer (Aggregated KPIs & Risk Analytics)      |
|                                                          │                                        |
|  [Orchestration & BI]                                    ▼                                        |
|  Airflow DAG ──► PostgreSQL Warehouse ──► Streamlit App & Tableau Live Connection                 |
+---------------------------------------------------------------------------------------------------+
```

---

## 🛠️ 4. Detailed Architectural Enhancements (Pillar by Pillar)

### Pillar 1: Data Model Expansion & Multi-Currency Handling
* **Multi-Entity Augmentation**:
  * **Branches Dimension**: 10–50 regional branches with staff counts, operating overhead, and regional manager metrics.
  * **Customer Profiles**: Enriched with credit scores, age group buckets, income segments, and account tiers (*Basic*, *Standard*, *Premium*).
  * **Loan Book**: Detailed loans (Home, Auto, Personal) tracking interest rates, outstanding balances, loan-to-value (LTV) ratios, and delinquency risk levels.
* **Multi-Currency & FX Processing**:
  * Ingests foreign currency transactions (USD, EUR, GBP) and applies real-time/daily FX exchange rate transformations to standardize all metrics to INR (₹).

---

### Pillar 2: Medallion Lakehouse ETL Pipeline (`Bronze` ➔ `Silver` ➔ `Gold`)

#### 🔶 1. Bronze Layer (`etl_raw_to_bronze.py`)
* **Purpose**: Ingest raw Kaggle CSV and streaming events, clean corrupt records, standardize timestamps, and write immutable Snappy-compressed Parquet / Apache Iceberg tables partitioned by `year/month`.

#### 🔶 2. Silver Layer (`etl_bronze_to_silver.py`)
* **Purpose**: Join transactions with Customer, Branch, and Loan dimension tables. 
* **Transformations**:
  * Calculate customer age, `age_group`, `income_segment`, and `balance_segment`.
  * Classify transactions as Income, Expense, Withdrawal, or Transfer.
  * Compute transaction fee costs (e.g. 10% or ₹5 fixed processing cost per transaction).

#### 🔶 3. Gold Layer (`etl_silver_to_gold.py`)
* **Purpose**: Compute high-level analytical business metrics:
  * **Branch Performance**: Total revenue, operating costs, net branch income, Cost-to-Income Ratio (CIR), and transactions per staff member.
  * **Customer Profitability**: Gross revenue, processing costs, net profit, profit margin %, and customer value tiers (*High Value* > 30% margin).
  * **Loan Portfolio Risk**: Total portfolio disbursed, outstanding balance, utilization rate, average interest rate, and risk category distributions.

---

### Pillar 3: Real-Time Event Streaming Layer (Kafka + Spark)
* **Kafka Producer (`scripts/kafka_producer.py`)**:
  * Publishes mock live transactions to topic `bank.transactions.v1` at configurable Transactions-Per-Second (TPS).
* **Spark Structured Streaming Consumer (`spark_jobs/streaming/kafka_stream_consumer.py`)**:
  * Consumes from Kafka using 10-minute watermarking (`.withWatermark("timestamp", "10 minutes")`).
  * Computes sliding 5-minute window aggregations (live TPS, sudden surge detection, transaction velocity).
  * Sinks data continuously to both the Bronze Lakehouse storage and PostgreSQL streaming tables.

---

### Pillar 4: Predictive Analytics Engine (PySpark MLlib)
* **Loan Default Risk Predictor (`spark_jobs/ml/loan_default_predictor.py`)**:
  * Trains a Gradient-Boosted Tree (GBT) classifier on Silver dataset features (credit score, income segment, outstanding balance, LTV ratio).
  * Outputs `default_probability` and `risk_rating` (*Low*, *Moderate*, *High*, *Critical*).
* **Fraud Anomaly Detection Simulation**:
  * Flags rapid high-value transactions or unusual geographic velocity during Silver transformation.

---

### Pillar 5: Data Quality Gates & Quarantine (Great Expectations)
* **In-Pipeline Quality Assertions**:
  * Checks non-null primary keys (`customer_id`, `transaction_id`).
  * Validates numeric bounds (`amount > 0`, `0% <= interest_rate <= 30%`).
  * Verifies referential integrity between transactions and customer dimensions.
* **Quarantine Layer (`data/quarantine/`)**:
  * Records failing quality gates are diverted to quarantine with metadata (`error_code`, `failed_timestamp`), preventing bad data from corrupting Gold tables or Airflow DAG execution.

---

### Pillar 6: Orchestration, Infrastructure & BI Layer
* **Airflow Orchestration (`revenue_cost_pipeline_dag.py`)**:
  * Manages task dependencies (`raw_to_bronze >> bronze_to_silver >> silver_to_gold >> data_quality_check`).
  * Includes automated retries (1 retry with 5-min delay), failure notifications, and Airflow File Sensors.
* **Streamlit & Tableau Dashboards**:
  * Streamlit web app with interactive Plotly heatmaps and drill-downs.
  * PostgreSQL semantic views (`vw_branch_performance`, `vw_customer_profitability`, `vw_loan_portfolio`) formatted for instant connection to Tableau Desktop / Public.

---

## 🗓️ 5. Step-by-Step Implementation Roadmap

```
  Phase 2.1: Data Quality & Schema Quarantine Gate Implementation
     └── Integrate Great Expectations validation checks in bronze_to_silver ETL.

  Phase 2.2: Real-Time Kafka Streaming Pipeline
     └── Add Kafka to docker-compose.yml, write Kafka Producer and Spark Structured Streaming job.

  Phase 2.3: PySpark MLlib Predictive Risk Engine
     └── Build & train Loan Default Risk scoring pipeline and append predictions to Gold tables.

  Phase 2.4: Tableau Connection & Executive Streamlit Dashboard Upgrade
     └── Connect Tableau to PostgreSQL warehouse views & enhance Streamlit interactive charts.
```
