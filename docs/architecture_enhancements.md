# Architecture Enhancements & Target Blueprint: Aura Bank Financial Analytics

This document outlines the required architectural enhancements to upgrade the **Aura Bank Financial Analytics** platform from a pure batch Data Lakehouse into an enterprise-grade **Hybrid Real-Time, Predictive, and Automated Data Engineering Platform**.

---

## 🎯 Executive Summary

The current architecture provides a robust batch Medallion Lakehouse (Bronze ➔ Silver ➔ Gold) with PostgreSQL warehousing, PySpark ETL, Airflow orchestration, and Streamlit visualization.

To fulfill the complete vision of a modern financial analytics architecture, four core architectural enhancements are specified:
1. **Real-Time Streaming Layer (Kafka + Spark Structured Streaming)**
2. **Predictive Analytics Layer (Spark MLlib Credit & Default Modeling)**
3. **Automated Data Quality & Quarantine Gates**
4. **Enhanced BI & Semantic Warehouse Layer (Tableau Integration)**

---

## 📊 Current vs. Target Architecture Comparison

| Architectural Pillar | Current Architecture (Phase 1) | Target Architecture (Phase 2 Upgrade) |
| :--- | :--- | :--- |
| **Ingestion Pattern** | Batch CSV file processing | **Hybrid**: Batch Lakehouse + Real-Time **Kafka** Event Streaming |
| **Processing Engine** | PySpark Batch ETL | PySpark Batch ETL + **Spark Structured Streaming** |
| **Analytics Capability** | Descriptive (KPIs, CIR, Margins) | **Predictive & Diagnostic** (Risk Scoring, Default Probability) |
| **Data Quality** | Post-execution verification script | **In-Pipeline Data Quality Gates** & Quarantine layer |
| **Warehouse Sinks** | PostgreSQL Batch Tables & Views | PostgreSQL Batch Views + **Real-Time Streaming Sinks** |
| **Visualization** | Streamlit Web App | Streamlit Web App + **Tableau Live Connector** |

---

## 🏗️ Detailed Architecture Enhancements

```
+-----------------------------------------------------------------------------------------------+
|                               TARGET HYBRID ARCHITECTURE BLUEPRINT                            |
|                                                                                               |
|  [Real-Time Event Sources]                                                                    |
|  Python Kafka Producer ──► Kafka Topic: bank-transactions ──► Spark Structured Streaming      |
|  (Simulated live txns)     (Partitioned / Distributed)        (Watermarking & Windows)        |
|                                                                     │                         |
|                                                                     ├──► Real-Time Stream Sink|
|                                                                     │    (Memory / Postgres)  |
|                                                                     │                         |
|  [Batch Processing Path]                                            ▼                         |
|  Kaggle + Synthetic ────► Bronze (Raw CSV) ─────────────► Silver (Parquet Lakehouse)         |
|                           (scripts/integrate)              │ (Schema & Cleaning)              |
|                                                            │                                  |
|                                                            ▼                                  |
|                                                    PySpark MLlib Engine                       |
|                                                    (Loan Default Risk & Churn)                |
|                                                            │                                  |
|                                                            ▼                                  |
|  [Warehouse & BI Layer]                               Gold (Aggregations & Risk)              |
|  Tableau / Streamlit App ◄── PostgreSQL Warehouse ◄────────┘ (PostgreSQL Loading)             |
+-----------------------------------------------------------------------------------------------+
```

---

## 🛠️ 1. Real-Time Event Streaming Layer (Kafka)

### Components & Technical Requirements:
* **Kafka Event Producer (`scripts/kafka_producer.py`)**:
  * Simulates live stream of customer transactions, branch expenses, and loan repayment events.
  * Configurable Transactions-Per-Second (TPS) rate and payload schema serialization (JSON / Avro).
* **Kafka Cluster Infrastructure**:
  * Topic 1: `bank.transactions.v1` (High throughput transaction events).
  * Topic 2: `bank.expenses.v1` (Branch operational expenses).
* **Spark Structured Streaming Job (`spark_jobs/streaming/kafka_stream_consumer.py`)**:
  * Consumes from Kafka topics with event time watermarking (`.withWatermark("timestamp", "10 minutes")`).
  * Windowed aggregations (5-minute sliding windows for branch transaction velocity).
  * Dual Sinks: Appends raw events to Bronze Parquet directory and writes streaming aggregates to PostgreSQL.

---

## 🤖 2. Predictive Analytics & Machine Learning Layer (Spark MLlib)

### Components & Technical Requirements:
* **Loan Default Risk Scoring Model (`spark_jobs/ml/loan_default_predictor.py`)**:
  * Uses Silver layer customer demographics, balance trends, and loan attributes to train a **Gradient-Boosted Tree (GBT)** classifier.
  * Predicts `default_probability` (0.0 to 1.0) and assigns a `risk_rating` (*Low*, *Moderate*, *High*, *Critical*).
* **Customer Lifetime Value (CLV) & Churn Scoring**:
  * Evaluates transaction frequency decay and balance drop-offs.
* **Pipeline Integration**:
  * ML inference runs as a PySpark transformation step during the Silver ➔ Gold batch pipeline, writing predictions directly into `gold/loan_risk_analytics` and PostgreSQL warehouse tables.

---

## 🛡️ 3. In-Pipeline Data Quality & Quarantine Gates

### Components & Technical Requirements:
* **Schema & Contract Enforcement**:
  * Standardizes strict PySpark StructType schemas before reading data into memory.
* **In-Memory Data Quality Validation (`spark_jobs/common/data_quality.py`)**:
  * Validates assertions: non-null primary keys (`customer_id`, `transaction_id`), positive monetary amounts, valid date formats.
* **Quarantine Layer (`data/quarantine/`)**:
  * Records failing validation rules are diverted to a dedicated quarantine directory with failure metadata (`error_code`, `failed_timestamp`), keeping production Lakehouse clean.

---

## 📊 4. Warehouse & BI Semantic Layer (Tableau Integration)

### Components & Technical Requirements:
* **Analytical Database Views**:
  * `vw_realtime_branch_tps`: Live transaction velocity per branch.
  * `vw_loan_risk_analytics`: Combines financial performance with ML default risk scores.
* **Tableau Connection Capabilities**:
  * Direct PostgreSQL JDBC/ODBC connector setup for Tableau Desktop and Tableau Public workbooks.
  * Pre-built workbook data source definitions with optimized index performance.

---

## 🗓️ Implementation Roadmap

```
  Phase 2.1: Data Quality Gates & Quarantine Engine
     └── Implement in-line assertions in PySpark Bronze-to-Silver ETL.

  Phase 2.2: Kafka Real-Time Ingestion Architecture
     └── Add Kafka container to docker-compose, build Python Producer & Spark Streaming Consumer.

  Phase 2.3: PySpark MLlib Predictive Engine
     └── Build & train Loan Default & Churn risk models, integrating outputs into Gold Layer.

  Phase 2.4: Tableau BI & Real-Time Dashboard Enhancement
     └── Expose real-time streaming & ML risk views to PostgreSQL & Tableau workbook connector.
```
