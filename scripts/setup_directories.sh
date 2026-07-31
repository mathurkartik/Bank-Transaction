#!/bin/bash

echo "🏦 Setting up Bank Financial Analytics Project..."

# Create directory structure
mkdir -p data/raw data/processed
mkdir -p spark_jobs/config spark_jobs/batch spark_jobs/streaming
mkdir -p airflow/dags sql_warehouse streamlit_app scripts

# Create data directories
mkdir -p warehouse/iceberg warehouse/checkpoints

echo "✅ Directory structure created!"
echo ""
echo "📁 Project Structure:"
echo "bank-financial-analytics/"
echo "├── data/raw/              # Place Kaggle CSV here"
echo "├── data/processed/        # Generated datasets"
echo "├── spark_jobs/           # ETL pipelines"
echo "├── airflow/dags/         # Workflow orchestration"
echo "├── sql_warehouse/        # Database schema"
echo "├── streamlit_app/        # Dashboard"
echo "└── scripts/              # Data generation"
echo ""
echo "🚀 Next steps:"
echo "1. Place Kaggle dataset in data/raw/"
echo "2. Run: docker-compose up -d"
echo "3. Run: python scripts/integrate_kaggle_synthetic.py"
