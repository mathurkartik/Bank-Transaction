# Business & Implementation Overview: Aura Bank Analytics Platform

## 🏦 1. Executive Business Overview

### 1.1 Business Context & Problem Statement
In retail banking, financial institutions face three major operational and profitability challenges:
1. **High Operational Overhead & Branch Inefficiency**: Branch networks account for over 60% of operating expenses. Without real-time visibility into branch-level Cost-to-Income Ratios (CIR), underperforming branches erode net profit margins.
2. **Delayed Credit Risk & NPA (Non-Performing Asset) Recognition**: Traditional credit risk reviews happen on a quarterly batch basis. By the time a loan is recognized as defaulted, recovery costs are high and capital buffers are damaged.
3. **Siloed Customer Data & Uncaptured Customer Lifetime Value (CLV)**: Customer profitability data is fragmented across deposit, card, and loan silos, preventing targeted product cross-selling to high-margin accounts.

### 1.2 The Solution: Aura Bank Analytics Platform
The **Aura Bank Executive Financial Analytics Platform** is a unified, real-time data product designed for Bank Executives (CXOs), Risk Officers, and Branch Managers. It consolidates transactions, loans, deposits, and operating expenses into an interactive live dashboard powered by a high-throughput streaming engine and machine learning risk models.

---

## 💰 2. Business Model & Financial Mechanics

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FINANCIAL MODEL STRUCTURE                                │
│                                                                                          │
│  REVENUE STREAMS                                                                         │
│  ├── 1. Loan Interest Income (Collected monthly on active Home/Car/Personal loans)       │
│  ├── 2. Interchange & Transaction Fees (₹15–₹50 earned per card purchase/UPI transaction)│
│  └── 3. Account Maintenance & Overdraft Penalties (₹100–₹300 per account)                │
│                                                                                          │
│  COST STRUCTURE                                                                          │
│  ├── 1. Fixed Branch Operating Overhead (Staff Salaries, Facilities, IT - 1.8x Metro)  │
│  ├── 2. Variable Transaction Processing Fees (₹5 per swiped transaction)                │
│  └── 3. Bad-Debt Provisioning Reserves (15% capital buffer for High-Risk loans)           │
│                                                                                          │
│  KEY KPI RATIO                                                                           │
│  └── Cost-to-Income Ratio (CIR) = Total Operating Costs / Gross Revenue (Target: < 50%) │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 3. Technical Implementation & Product Architecture

The system is engineered using a modern **Medallion Data Lakehouse** architecture paired with **Real-Time Streaming** and **Multi-Cloud Hosting**:

```
+-----------------------------------------------------------------------------------------------+
|                               PRODUCT & DATA LAKEHOUSE ARCHITECTURE                           |
|                                                                                               |
|  [Ingestion & Real-Time Streaming Layer]                                                      |
|  ├── Kaggle 1.04M Transaction Base Data + Dynamic Incremental Generator                       |
|  └── Apache Kafka Event Producer (450 txns/min ~ 7.5 TPS with UUIDv4 cryptographic keys)      |
|                                         │                                                     |
|                                         ▼                                                     |
|  [Medallion Storage & Compute Layer]                                                          |
|  ├── BRONZE: Raw Ingestion & Immutable Data Storage (MinIO Local S3 / s3a://)                |
|  ├── SILVER: PySpark In-Pipeline Data Quality Engine & Quarantine Routing (`data/quarantine`) |
|  └── GOLD:   PySpark MLlib Loan Default Risk Classifier (GBT/Logistic Regression) & Aggregates|
|                                         │                                                     |
|                                         ▼                                                     |
|  [Data Serving & Cloud Deployment Layer]                                                      |
|  ├── Render Cloud: Python FastAPI REST Service (`api/main.py` on `aura-bank-api.onrender.com`) |
|  └── Vercel Cloud: Live Web Dashboard (`web_dashboard/` on `bank-transaction-six.vercel.app`)  |
+-----------------------------------------------------------------------------------------------+
```

### 3.1 Key Implementation Modules

1. **Incremental Data Generator & Expansion Engine** ([`scripts/integrate_kaggle_synthetic.py`](file:///c:/Users/KartikMathur/Desktop/Project/M5/scripts/integrate_kaggle_synthetic.py)):
   - Simulates **monthly branch network expansion (+2 branches/month)** from 50 to 62+ regional branches with Metro 1.8x operational cost multipliers.
   - Generates **widespread daily customer onboarding (+30–40 new accounts/day)** distributed evenly across all branches.
   - Models loan disbursals, EMI repayment streams, and default delinquency statuses.

2. **High-Volume Real-Time Kafka Stream Producer** ([`scripts/kafka_producer.py`](file:///c:/Users/KartikMathur/Desktop/Project/M5/scripts/kafka_producer.py)):
   - Emits live events at **450 transactions/minute (7.5 TPS)** with 128-bit UUIDv4 cryptographic primary keys.
   - Emits 4 live banking event types: `CARD_TRANSACTION`, `CUSTOMER_ONBOARDED`, `EMI_PAYMENT_EVENT`, `NEW_BRANCH_OPENED`.

3. **Data Quality & Quarantine Engine** ([`spark_jobs/common/data_quality.py`](file:///c:/Users/KartikMathur/Desktop/Project/M5/spark_jobs/common/data_quality.py)):
   - Enforces automated validation gate rules during PySpark ETL. Invalid or corrupted records are quarantined to `data/quarantine/` for compliance auditability.

4. **PySpark MLlib Predictive Default Risk Engine** ([`spark_jobs/ml/loan_default_predictor.py`](file:///c:/Users/KartikMathur/Desktop/Project/M5/spark_jobs/ml/loan_default_predictor.py)):
   - Trains a Gradient Boosted Trees (GBT) classifier to evaluate loan portfolios and categorize loan risk into *Low Risk*, *Moderate Risk*, *High Risk*, and *Critical Risk*.

5. **Cloud Deployment Infrastructure**:
   - **Backend (Render)**: Python FastAPI REST API (`api/main.py`) serving live executive metrics with dynamic simulation fallback.
   - **Frontend (Vercel)**: Glassmorphism dark-mode live dashboard (`web_dashboard/index.html`) polling API endpoints every 5 seconds.

---

## 📊 4. Technical Design Decisions & Trade-offs

| System Requirement | Technical Solution Chosen | Design Decision & Architectural Trade-off |
| :--- | :--- | :--- |
| **Data Provenance & Trust** | REST Endpoints + Fallback Banner | Explicitly flags when data is synthetic or fallback demo mode (`⚠️ NOTICE: DEMO DATASET IS SYNTHETICALLY DERIVED`) to maintain transparency. |
| **Real-Time Event Streaming** | Apache Kafka Producer & Spark Streaming | ~7.5 TPS is well below the threshold (~1,000+ TPS) where real-time streaming earns its operational cost over batch; used strictly to demonstrate streaming semantics (watermarking, sliding windows). |
| **Data Quality & Compliance** | PySpark In-Pipeline Quality Gate | Quarantines bad records to `data/quarantine/` instead of dropping them. Preserves audit lineage at the cost of storage & pipeline complexity. |
| **Lakehouse Governance** | 3-Tier Medallion Architecture (Bronze/Silver/Gold) | Isolates raw data, cleansed entities, and business aggregations. Improves governance at the cost of duplicate storage and multi-stage compute latency. |
| **High Availability** | Render Cloud + Fast API Service | Provides high availability for web demo purposes; fallback simulation guarantees uptime when persistent warehouse storage is unattached. |
