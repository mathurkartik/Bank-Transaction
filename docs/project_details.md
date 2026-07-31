# Aura Bank Financial Analytics - Project Details & Architecture

This document provides a comprehensive overview of the **Aura Bank Financial Analytics Data Lake** project, detailing the system goals, architecture, ingestion flow, schema structures, and analytical directions.

---

## 🎯 Project Goal & Summary

* **Goal**: Build a unified data lake for financial performance analytics across multiple departments.
* **Core Tech Flow**:
  * **Kafka / Ingestion**: Stream operational data (transactions, expenses, fees). *Note: Local development leverages files and simulated integrations.*
  * **Spark Batch Jobs**: Perform data cleaning, reconciliation, currency conversions, and create dimensional models (`fact_revenue`, `dim_branch`, `dim_product`, and analytical layers).
  * **SQL Warehouse**: Store and expose curated datasets (PostgreSQL warehouse).
  * **Python + Airflow**: Orchestrate daily data refreshes and pipelines.
  * **Tableau / Visualization**: Expose KPIs (Net Interest Margin, Cost-Income Ratio, Branch Performance, Product Profitability) in interactive dashboards (implemented locally via Streamlit + Plotly).
* **Key Skills Demonstrated**: Data warehousing, Spark ETL, financial KPI modeling, multi-source data integration.

---

## 🏗️ 1. Technical Architecture & Tech Stack

The platform is designed as a local **modern data lakehouse** that processes over 1.7 million rows of transactions and customer data to evaluate branch efficiency, customer lifetime value/profitability, and loan book credit risks.

* **Storage Layer**: Directory-based Lakehouse structure (raw ➔ processed ➔ silver ➔ gold).
* **Processing Engine**: **Apache PySpark (3.5.x)** for vectorized, high-performance distributed computations.
* **Orchestration**: **Apache Airflow (2.8.1)** containerized with a PostgreSQL metadata backend.
* **Database (Warehouse)**: **PostgreSQL (13)** database containing schemas and analytical views.
* **Visualization Layer**: **Streamlit** dark-mode web application utilizing **Plotly** for responsive dashboards.

```
+-------------------------------------------------------+
| Ingestion & In-memory Processing                      |
| (integrate_kaggle_synthetic.py)                      |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
| Lakehouse Ingestion Directory                         |
| (data/raw -> data/processed)                          |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
| Bronze-to-Silver PySpark ETL                          |
| (data/silver Parquet partitioned formats)             |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
| Silver-to-Gold PySpark ETL                            |
| (data/gold Parquet & PostgreSQL Tables)               |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
| Warehouse Views & Streamlit Dashboard Visuals          |
+-------------------------------------------------------+
```

---

## 📊 2. The Data Journey (Lakehouse Layers)

### Layer 1: Raw & Processed (Ingestion)
* **Main Source**: Kaggle's `bank_transactions.csv` (1,048,567 raw transactions containing account balances, transaction dates, transaction locations, and customer dates of birth).
* **Extensions**: The integration script cleans the Kaggle source, maps locations to 50 physical branches, and creates consistent synthetic datasets representing credit lines, bank revenue events, and operating costs.
* **Outputs** (`data/processed/`):
  * `customers.csv` (884k customer profiles)
  * `transactions.csv` (1.75M transaction history)
  * `revenue.csv` (1.23M bank fee events)
  * `costs.csv` (919 branch cost entries)
  * `loans.csv` (176k active and closed credit loans)
  * `branches.csv` (50 regional branch details)

### Layer-2: Silver Layer (Cleaning & Enrichment)
PySpark reads the processed CSV files, enforces schema types (handling missing dates/location values), and enriches the records:
* **Customers**: Calculates ages and maps customers to `age_group` (18-24, 25-34, etc.), `income_segment` (Low/Medium/High), and `balance_segment` (Low/Medium/High).
* **Transactions**: Standardizes timestamps to dates, identifies debit/credit tags, and groups transaction amounts into `amount_category` (Small/Medium/Large).
* **Format**: Writes out partition-optimized Snappy-compressed **Parquet** files to `data/silver/`.

### Layer-3: Gold Layer (Aggregations & KPIs)
PySpark reads the Silver Parquet datasets and rolls them up into target analytical tables:
* **Customer Profitability**: Sums transaction revenues per customer, subtracts transaction processing costs, and computes net profit and profit margin percentages.
* **Branch Performance**: Aggregates total transaction counts and revenues, merges branch operating cost categories, and calculates net branch income and cost-to-income ratios.
* **Loan Portfolio**: Groups active loans to calculate outstanding balances, regional exposure, and average interest rates.
* **Format**: Saves Parquets to `data/gold/` and writes to the `bank_dwh` schema in PostgreSQL.

---

## 💾 3. Data Warehouse Schema & Views

### Table 1: `customer_profitability`
Evaluates individual customer financial contribution:
* `customer_id` (PK) - Key identifier (e.g., `KAGGLE_C1234567`)
* `customer_segment` - BASIC, STANDARD, or PREMIUM (determined by account balance)
* `total_revenue` - Total transaction fees and interest income collected from the customer
* `estimated_costs` - Cost of processing the customer's transactions (₹5 per txn)
* `net_profit` - `total_revenue - estimated_costs`
* `profit_margin` - `net_profit / total_revenue`
* **Extended View (`vw_customer_profitability`)**:
  * Adds `value_tier`: *High Value* (margin > 30%), *Medium Value* (margin > 10%), or *Low Value*.

### Table 2: `branch_performance`
Measures operational productivity of the bank's 50 physical branches:
* `branch_id` (PK) - Key identifier (e.g., `BR_001` to `BR_050`)
* `total_revenue` - Gross revenue collected from transactions and accounts assigned to the branch
* `total_costs` - Salaries, facilities, and technology costs of the branch
* `net_income` - `total_revenue - total_costs`
* `cost_income_ratio` - `total_costs / total_revenue`
* `transaction_count` - Total transaction throughput
* `transaction_per_staff` - Average transaction volume per staff member
* **Extended View (`vw_branch_performance`)**:
  * Adds `efficiency_rating`: *Excellent* (< 50% CIR), *Good* (< 60%), *Fair* (< 70%), or *Needs Improvement*.
  * Adds `productivity_rating`: *High*, *Medium*, or *Low* staff productivity.

### Table 3: `loan_portfolio`
Tracks credit book and outstanding risk:
* `branch_id` (PK) - Identifies branch managing the loan
* `total_loan_portfolio` - Total principal capital disbursed
* `total_outstanding` - Outstanding debt balances currently held
* `avg_interest_rate` - Mean interest rate of active loans
* `active_loans` - Total count of open loans
* **Extended View (`vw_loan_portfolio`)**:
  * Adds `utilization_rate`: `total_outstanding / total_loan_portfolio`
  * Adds `rate_category`: *High*, *Medium*, or *Low* interest bands.

---

## 💡 4. Potential Insight & Analytical Directions

1. **Operating Efficiency Analysis**:
   * Which branches have a high cost-to-income ratio (CIR > 70%) despite high transaction volumes? Is it driven by facility costs or staffing?
   * How does employee productivity (transactions per staff) correlate with branch net income?
2. **Customer Lifetime Value & Churn Risk**:
   * What percentage of our customer base falls in the "Low Value" tier? Are they consuming resources (high txn counts) while generating low revenue?
   * Which customer demographics (age group, city location) are most represented in the "High Value" (Premium) segment?
3. **Credit Risk & Loan Health**:
   * Which branches have a dangerously high loan utilization rate (> 80% of loan book is outstanding)?
   * How does the average interest rate at a branch affect loan volume and delinquency rate?
4. **Product Cross-Selling opportunities**:
   * How many high-balance customer profiles (PREMIUM) do not currently hold an active loan product? (Target list generation for marketing).
