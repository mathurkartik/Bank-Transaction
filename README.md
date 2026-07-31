

# 🏦 Aura Bank Financial Analytics Platform

A complete financial data lake and analytics platform running locally in Docker. This platform integrates Kaggle customer segmentation data with synthetic financial transactions, processes it using PySpark, schedules via Apache Airflow, stores it in PostgreSQL, and visualizes it in a high-fidelity Streamlit dashboard.

---

## 🏗️ Architecture

1. **Data Ingestion**: Kaggle Bank Transactions + Synthetic Extensions (loans, revenues, costs, extra transactions)
2. **Lakehouse Layers**:
   - **Bronze**: Raw data cleanup and dtype conversion
   - **Silver**: Enriched data, segmentation (income, balances, age groups)
   - **Gold**: High-value business KPIs and aggregations (margins, cost-to-income ratios)
3. **Data Warehouse**: PostgreSQL database storing Gold KPIs and creating analytical views
4. **Visualisation**: Streamlit web application with premium glassmorphism dark aesthetic

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have the following installed on your host:
- Docker Desktop
- Python 3.9+
- The Kaggle Bank Customer Segmentation dataset (`bank_transactions.csv`)

### 2. Set Up Project Directories
Create the required directory structure:
**On Linux/Mac (Bash):**
```bash
chmod +x scripts/setup_directories.sh
./scripts/setup_directories.sh
```

**On Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "data/raw", "data/processed", "spark_jobs/config", "spark_jobs/batch", "spark_jobs/streaming", "airflow/dags", "sql_warehouse", "streamlit_app", "scripts", "warehouse/iceberg", "warehouse/checkpoints", "airflow/logs"
```

### 3. Add Kaggle Dataset
Place your downloaded Kaggle `bank_transactions.csv` file into the `data/raw/` folder.

### 4. Build and Start Services
This project uses a custom Dockerfile to bundle Java (JDK 17) and the Python dependencies (PySpark, Pandas) into the Airflow containers.

Start the services with:
```bash
docker-compose up -d --build
```
*Note: The `--build` flag ensures our custom Airflow image is built.*

### 5. Generate and Integrate Synthetic Data
Generate the data models (on your host machine):
```bash
pip install pandas numpy faker python-dateutil
python scripts/integrate_kaggle_synthetic.py
```
This creates the full dataset inside `data/processed/`.

### 6. Run the ETL Pipeline
1. Open the Airflow Webserver: http://localhost:8080
2. Login credentials: `admin` / `admin`
3. Locate the `financial_analytics_pipeline` DAG and trigger it.
4. The pipeline will clean the datasets, write them as Parquet files (Silver/Gold layers), and import the metrics to the PostgreSQL warehouse.

### 7. Launch Dashboard
Open the Streamlit application: http://localhost:8501
- If the database ETL has not run yet, the dashboard will gracefully fall back to displaying mock high-fidelity sample data.
- Once the database is populated, it will pull the metrics from the SQL views.

---

## 🛠️ Technology Stack
- **Data Lake Engine**: PySpark (local mode)
- **Orchestrator**: Apache Airflow 2.8.1 (SequentialExecutor + SQLite metadata)
- **Data Warehouse**: PostgreSQL 13
- **Visualization**: Streamlit 1.28.0 + Plotly
- **Environment**: Docker & Docker Compose




 
