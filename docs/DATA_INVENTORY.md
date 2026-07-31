# Data Inventory & Schema Reference

> **Document Purpose**: This document provides a complete inventory and schema data dictionary of all **Raw Input Data** and **Synthetically Generated Data** present in the Aura Bank Financial Analytics platform.

---

## 📌 1. Data Provenance & Boundary Summary

| Data Category | Storage Location | Source Type | Description |
| :--- | :--- | :--- | :--- |
| **Raw Base Data** | `data/raw/bank_transactions.csv` | **`[REAL KAGGLE BASE]`** | 1,048,567 real Kaggle bank transaction records across 884,265 unique customers. |
| **Processed Entity Data** | `data/processed/` | **`[SYNTHETIC DERIVED]`** | 6 core relational entity CSV datasets generated from the real Kaggle base. |
| **Silver Lakehouse Data** | `data/silver/` & `data/quarantine/` | **`[DERIVED LAKEHOUSE]`** | Deduplicated Parquet tables with quality-gate quarantine routing. |
| **Gold Analytics & ML Data** | `data/gold/` | **`[DERIVED GOLD/ML]`** | Business KPI aggregations and PySpark ML default risk model output datasets. |

---

## 📥 2. Raw Input Dataset `[REAL KAGGLE BASE]`

### File: `data/raw/bank_transactions.csv`
* **Source**: Real Kaggle Bank Customer Transaction Dataset
* **Record Count**: `1,048,567 rows` `[REAL]`
* **Unique Customers**: `884,265` `[REAL]`

| Field Name | Data Type | Null Count | Real/Synthetic | Field Description |
| :--- | :--- | :--- | :--- | :--- |
| `TransactionID` | String | 0 (100.0%) | **`[REAL]`** | Original transaction unique identifier. |
| `CustomerID` | String | 0 (100.0%) | **`[REAL]`** | Original customer unique identifier. |
| `CustomerDOB` | String | 3,397 (99.68%) | **`[REAL]`** | Customer date of birth as recorded in Kaggle base. |
| `CustGender` | String | 1,100 (99.90%) | **`[REAL]`** | Customer gender (`M` / `F`). |
| `CustLocation` | String | 151 (99.99%) | **`[REAL]`** | Customer location / city string. |
| `CustAccountBalance` | Float64 | 2,369 (99.77%) | **`[REAL]`** | Customer account balance in INR. |
| `TransactionDate` | String | 0 (100.0%) | **`[REAL]`** | Transaction date (`DD/MM/YY`). |
| `TransactionTime` | Int64 | 0 (100.0%) | **`[REAL]`** | Transaction time in seconds/HHMMSS integer. |
| `TransactionAmount (INR)`| Float64 | 0 (100.0%) | **`[REAL]`** | Transaction amount in INR (Mean: ₹1,574.34, Median: ₹459.03). |

---

## ⚙️ 3. Processed & Synthetically Derived Datasets `[SYNTHETIC]`

The following 6 CSV datasets are produced in `data/processed/` by [`scripts/integrate_kaggle_synthetic.py`](file:///c:/Users/KartikMathur/Desktop/Project/M5/scripts/integrate_kaggle_synthetic.py):

### 3.1 `data/processed/customers.csv` `[SYNTHETIC DERIVED]`
* **Purpose**: Customer profiles enriched with credit scores and income segments.
* **Fields**:
  - `customer_id` (String): Primary key (`KAGGLE_C100001` or `CUST-8F92A1C490`).
  - `original_customer_id` (String): Reference to raw Kaggle customer ID.
  - `first_name` / `last_name` (String): Synthetically sampled Indian customer names.
  - `age` (Int): Customer age calculated from DOB or sampled (18–75).
  - `gender` (String): Cleaned gender (`M` / `F`).
  - `city` / `country` (String): Residential city and country (`India`).
  - `account_balance` (Float): Account balance in INR.
  - `customer_segment` (String): `BASIC` (<₹1L), `STANDARD` (₹1L–₹5L), `PREMIUM` (>₹5L).
  - `credit_score` (Int): Credit score sampled from Gaussian distribution (350–800).
  - `annual_income` (Int): Estimated annual income correlated with account balance.
  - `customer_since` (Date): Account opening date.

---

### 3.2 `data/processed/transactions.csv` `[SYNTHETIC DERIVED]`
* **Purpose**: 1-year historical transaction ledger combining original and synthetic swipes.
* **Fields**:
  - `transaction_id` (String): Primary key (`TXN-D3B07384D113`).
  - `customer_id` (String): Foreign key to `customers.csv`.
  - `account_id` (String): Foreign key to bank account (`ACC_100001`).
  - `amount` (Float): Transaction amount in INR (always > 0).
  - `transaction_type` (String): `DEPOSIT`, `WITHDRAWAL`, `TRANSFER`, `PAYMENT`, `PURCHASE`.
  - `category` (String): Expense category (`GROCERIES`, `UTILITIES`, `ELECTRONICS`, etc.).
  - `merchant` (String): Merchant name or `BANK_CREDIT`.
  - `timestamp` (Date): Date of transaction.
  - `branch_id` (String): Regional branch ID (`BR_001` to `BR_062`).
  - `currency` (String): `INR`.

---

### 3.3 `data/processed/revenue.csv` `[SYNTHETIC DERIVED]`
* **Purpose**: Fee collection and interest revenue streams for bank profit calculations.
* **Fields**:
  - `revenue_id` (String): Primary key (`REV_0000001`).
  - `customer_id` / `account_id` (String): Customer and account identifiers.
  - `revenue_type` (String): `ACCOUNT_MAINTENANCE_FEE`, `TRANSACTION_FEE`, `INTEREST_INCOME`, `LATE_FEE`.
  - `amount` (Float): Revenue collected in INR.
  - `event_date` (Date): Event date.
  - `branch_id` (String): Associated branch office ID.
  - `description` (String): Event description.

---

### 3.4 `data/processed/costs.csv` `[SYNTHETIC DERIVED]`
* **Purpose**: Operating expenses breakdown per branch office.
* **Fields**:
  - `cost_id` (String): Primary key (`COST_001_001`).
  - `branch_id` (String): Associated branch office ID (`BR_001` to `BR_062`).
  - `cost_category` (String): `STAFF_SALARIES`, `FACILITIES`, `TECHNOLOGY`, `MARKETING`, `COMPLIANCE`.
  - `amount` (Float): Cost amount in INR (1.8x multiplier applied for Metro branches `BR_001`–`BR_009`).
  - `cost_date` (Date): Date of expense.
  - `region` (String): Geographical region (`NORTH`, `SOUTH`, `EAST`, `WEST`).

---

### 3.5 `data/processed/loans.csv` `[SYNTHETIC DERIVED]`
* **Purpose**: Active and closed loan portfolios with interest rates and default statuses.
* **Fields**:
  - `loan_id` (String): Primary key (`LOAN_000001`).
  - `customer_id` (String): Borrower customer ID.
  - `loan_amount` (Float): Principal loan amount disbursed (₹1,00,000 to ₹20,00,000).
  - `outstanding_balance` (Float): Remaining principal balance.
  - `interest_rate` (Float): Risk-adjusted interest rate (8.5% to 18.0%, correlated with credit score).
  - `loan_type` (String): `HOME_LOAN`, `PERSONAL_LOAN`, `CAR_LOAN`, `EDUCATION_LOAN`.
  - `start_date` (Date): Loan sanction date.
  - `term_months` (Int): Loan term (12, 24, 36, 60, 84 months).
  - `status` (String): `ACTIVE` or `CLOSED`.
  - `branch_id` (String): Originating branch office ID.

---

### 3.6 `data/processed/branches.csv` `[SYNTHETIC DERIVED]`
* **Purpose**: Master dimension table of 62 regional branch offices across India.
* **Fields**:
  - `branch_id` (String): Primary key (`BR_001` to `BR_062`).
  - `branch_name` (String): Branch name (e.g. `Mumbai Main Branch`).
  - `city` / `country` (String): Location city and `India`.
  - `region` (String): `NORTH`, `SOUTH`, `EAST`, `WEST`.
  - `opening_date` (Date): Branch establishment date (includes +2 branches/month expansion).
  - `branch_manager` (String): Assigned branch manager name.
  - `staff_count` (Int): Staff headcount (8 to 50 employees).
  - `monthly_operating_cost` (Float): Base monthly operating cost budget in INR.

---

## 🏛️ 4. Lakehouse Derived Analytical Datasets `[DERIVED]`

### 4.1 Silver Cleansed Tables (`data/silver/`)
* Parquet tables (`customers`, `transactions`, `revenue`, `costs`, `loans`) cleansed and deduplicated by PySpark Data Quality Gates.
* Invalid records (e.g., negative amounts or missing primary keys) are routed to **`data/quarantine/`**.

### 4.2 Gold Analytical Datasets & Views (`data/gold/`)
* **`branch_performance`**: Branch-level Gross Revenue, Total Operating Costs, Net Profit, and Cost-to-Income Ratio (CIR).
* **`customer_profitability`**: Customer revenue, estimated service costs, net profit, and profit margin tiers (*High Value* >30% margin).
* **`loan_portfolio`**: Aggregated loan book values, active loan counts, and average interest rates.
* **`loan_risk_analytics`**: PySpark MLlib GBT default risk model predictions (*Low Risk*, *Moderate Risk*, *High Risk*, *Critical Risk*).
