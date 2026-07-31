import pytest
import os
import pandas as pd

def test_processed_data_files_exist():
    """Verify that all 6 core processed data files exist."""
    data_dir = "data/processed"
    required_files = ["customers.csv", "transactions.csv", "revenue.csv", "costs.csv", "loans.csv", "branches.csv"]
    for file in required_files:
        filepath = os.path.join(data_dir, file)
        assert os.path.exists(filepath), f"Required file missing: {filepath}"

def test_customers_data_integrity():
    """Verify customer profiles schema and primary key uniqueness."""
    customers = pd.read_csv("data/processed/customers.csv")
    assert not customers.empty, "Customers dataframe is empty"
    assert "customer_id" in customers.columns, "customer_id column missing"
    assert customers["customer_id"].is_unique, "customer_id contains non-unique values"
    assert (customers["account_balance"] >= 0).all(), "Found negative account balance"

def test_transactions_data_integrity():
    """Verify Silver transaction records schema and quality gate non-negative amounts."""
    transactions = pd.read_parquet("data/silver/transactions")
    assert not transactions.empty, "Silver transactions dataframe is empty"
    assert "transaction_id" in transactions.columns, "transaction_id column missing"
    assert "amount" in transactions.columns, "amount column missing"
    assert (transactions["amount"] > 0).all(), "Found non-positive transaction amounts in Silver layer"

def test_gold_ml_analytics_exist():
    """Verify that PySpark ML Gold analytics Parquet output exists."""
    gold_ml_path = "data/gold/loan_risk_analytics"
    assert os.path.exists(gold_ml_path), "Gold loan risk analytics output directory missing"
