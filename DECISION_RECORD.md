# Product & Architectural Decision Record (ADR)

> **Document Purpose**: This document records the product, architectural, and data engineering decisions made in this repository. It serves as a transparent Technical Product Management (TPM) portfolio artifact documenting design trade-offs, trust corrections, real-data grounding, and model boundary conditions.

---

## 1. Context & Honesty Note

### Data Provenance & Boundaries
* **Real Base Data**: The base transaction dataset (`data/raw/bank_transactions.csv`) consists of **1,048,567 real Kaggle transactions** across **884,265 unique customer IDs**.
* **Synthetic Derived Data**: All downstream labels and extensions—including loan default labels (`risk_category`), monthly branch expansion events (+2/month), widespread daily customer onboarding (+30–40/day), and EMI repayment streams—are **synthetically generated**.
* **Portfolio Scope**: This repository is a **Technical PM Learning & Evaluation Artifact**, not a production banking software product. 
* **What This Artifact Proves**: Demonstrates end-to-end data pipeline orchestration (Apache Spark, Kafka), schema governance (Medallion architecture), API integration (FastAPI), cloud deployment (Render, Vercel), and product-level decision-making.
* **What This Artifact Does NOT Prove**: Does not prove real-world credit risk predictive accuracy or commercial production viability without real bank financial statements.

---

## 2. Design Decisions & Architectural Trade-offs

### Decision 1: Data Quality Quarantine vs. Silent Record Dropping
* **Context**: Pipeline ingestion occasionally encounters invalid, malformed, or out-of-range records (e.g. non-positive transaction amounts, missing primary keys).
* **Choice**: Implemented an in-pipeline Data Quality Gate ([`spark_jobs/common/data_quality.py`](file:///c:/Users/KartikMathur/Desktop/Project/M5/spark_jobs/common/data_quality.py)) that isolates non-compliant records into `data/quarantine/` instead of silently dropping them.
* **Trade-off**: 
  * *Benefit*: Preserves regulatory auditability, data lineage, and root-cause inspection required by banking compliance teams.
  * *Cost*: Increases downstream storage overhead and pipeline complexity compared to silently dropping bad records via `df.dropna()`.

---

### Decision 2: Medallion Architecture Depth (Bronze ➔ Silver ➔ Gold)
* **Context**: Structuring raw transaction data into downstream analytical layers.
* **Choice**: Adopted a 3-tier Medallion Lakehouse pattern (Bronze: raw storage; Silver: cleansed/deduplicated tables; Gold: aggregated business KPIs and ML features).
* **Trade-off**:
  * *Benefit*: Clear separation of concerns, data governance, and reusability across multiple downstream consumers (BI, ML, Reporting).
  * *Cost*: Introduces data storage redundancy (duplicating records across layers) and multi-stage compute latency compared to a single-layer direct warehouse load.

---

### Decision 3: Apache Kafka Event Streaming at ~7.5 TPS
* **Context**: Choice of event streaming mechanism for real-time transaction ingestion.
* **Choice**: Implemented an Apache Kafka Producer (`scripts/kafka_producer.py`) and Spark Structured Streaming consumer (`spark_jobs/streaming/kafka_stream_consumer.py`) operating at ~7.5 TPS (450 transactions/minute).
* **Honest Evaluation**: State honestly that ~7.5 TPS is well below where real-time event streaming is operationally or economically justified over scheduled batch processing. Kafka was used in this artifact strictly to learn and demonstrate real-time streaming semantics (watermarking, 5-minute sliding windows, stateful aggregations).
* **Justified Trigger**: The decision to stream rather than batch is driven by the downstream consumer's latency requirement, not by a throughput number. Streaming earns its operational and infrastructure cost only when a consumer has a latency SLA that scheduled batch cannot meet — e.g. instant automated fraud-blocking or real-time balance updates. At this artifact's volume, with no such sub-second SLA, batch processing would be the correct production choice; Kafka was used here strictly to learn streaming semantics.

---

## 3. What I'd Change / What Was Corrected

### 3.1 Corrected Trust Failure: Silent Synthetic Fallback
* **Initial Behavior**: When the backend REST API was offline or unpopulated, the web dashboard automatically rendered fallback simulated numbers without notifying the user.
* **Trust Impact**: In a financial analytics dashboard, silent data fabrication is a critical trust failure. Executives and risk officers must always know if data is live, stale, or synthetic.
* **Correction Applied**: Updated [`web_dashboard/index.html`](file:///c:/Users/KartikMathur/Desktop/Project/M5/web_dashboard/index.html) to display a prominent, unambiguous notification banner:  
  `⚠️ NOTICE: DEMO DATASET IS SYNTHETICALLY DERIVED (FALLBACK DEMO MODE)`.

---

## 4. Bounding the PySpark ML Default Classifier

### Model Boundary Statement
Because the loan default labels (`status` / `risk_category`) are synthetically generated from credit score rules, **any accuracy figure produced by the PySpark ML model is circular by construction**. Therefore, the PySpark ML default classifier in `spark_jobs/ml/loan_default_predictor.py` is a **PIPELINE-INTEGRATION DEMO ONLY**, demonstrating PySpark MLlib feature vectorization, GBT model training, and prediction pipeline mechanics.

### How a Production Version Would Be Validated
In a production commercial bank environment, credit risk models are validated through:
1. **Historical Backtesting**: Evaluating predictions against actual realized loan defaults over a 3-to-5 year macroeconomic cycle.
2. **Asymmetric False-Negative Cost**: Accounting for asymmetric loss functions—misclassifying a defaulting loan (False Negative) costs 10x–50x more in lost principal than misclassifying a good loan (False Positive).
3. **Operating Threshold Tuning**: Optimizing model thresholds based on Precision/Recall trade-offs (e.g. optimizing $F_2$ score to prioritize recall).
4. **Drift Monitoring**: Continuous monitoring for Population Stability Index (PSI) and Characteristic Stability Index (CSI) to detect feature and concept drift.

---

## 5. Honest Productisation & Stakeholder Target

* **Real Stakeholders**: The primary buyer and user of a Medallion Lakehouse & Risk Engine is a **Chief Data Officer (CDO)** or **Chief Risk Officer (CRO)**, not a Chief Product Officer (CPO).
* **True Success Metrics**: In risk & data engineering, success is measured by **provisioning accuracy, audit-readiness, data lineage traceability, and pipeline idempotency**—not dashboard render speed or UI animations.

---

## 6. Real-Data Grounding (Kaggle Base Un-derived Ground Truth)

The following metrics are computed directly by [`scripts/profile_real_base.py`](file:///c:/Users/KartikMathur/Desktop/Project/M5/scripts/profile_real_base.py) from the genuine, un-derived Kaggle raw base CSV (`data/raw/bank_transactions.csv`):

### Genuine Real Fields in Base Dataset (9 Fields)
* `TransactionID`, `CustomerID`, `CustomerDOB`, `CustGender`, `CustLocation`, `CustAccountBalance`, `TransactionDate`, `TransactionTime`, `TransactionAmount (INR)`

### Ground-Truth Descriptive Statistics `[REAL KAGGLE BASE DATA]`
* **Total Raw Record Count**: `1,048,567 rows` `[REAL]`
* **Unique Customer IDs**: `884,265` `[REAL]`
* **Aggregate Real Transaction Volume**: `INR 1,650,795,731.57` `[REAL]`
* **Mean Real Transaction Amount**: `INR 1,574.34` `[REAL]`
* **Median Real Transaction Amount**: `INR 459.03` `[REAL]`
* **Observation — Right-Skew**: The mean (INR 1,574.34) sits ~3.4x above the median (INR 459.03), indicating a heavy right-skew where a thin tail of large transactions drags the average well above the typical customer. Design consequence: any risk or alerting threshold keyed to the mean transaction size will misfire; a production rule should key to the median or to percentile bands, not the arithmetic mean.

*(Note: All other fields—such as loan risk categories, branch expansion events, and EMI payment streams—are synthetically derived extensions.)*

---

## 7. What I'd Build Next — and Why I Stopped Here

The obvious next step would be to replace synthetic default labels with a real backtest harness against historical defaults, and to add a proper feature store. I deliberately stopped short of this: the marginal engineering would not change what this artifact is meant to prove (pipeline orchestration and product-technical decision-making), and the effort was better allocated elsewhere. Knowing where additional build stops adding signal is itself the product decision.
