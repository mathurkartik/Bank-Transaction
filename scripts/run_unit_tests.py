import os
import pandas as pd
import sys

def run_tests():
    print("==========================================")
    print("[TESTS] RUNNING AUTOMATED UNIT & INTEGRITY TESTS")
    print("==========================================")
    
    passed = 0
    failed = 0
    
    # Test 1: Data Files Exist
    try:
        data_dir = "data/processed"
        required_files = ["customers.csv", "transactions.csv", "revenue.csv", "costs.csv", "loans.csv", "branches.csv"]
        for file in required_files:
            filepath = os.path.join(data_dir, file)
            assert os.path.exists(filepath), f"Missing required file: {filepath}"
        print("[PASSED] TEST 1: All 6 processed data files exist.")
        passed += 1
    except Exception as e:
        print(f"[FAILED] TEST 1: {e}")
        failed += 1

    # Test 2: Customer Data Uniqueness & Positive Balances
    try:
        customers = pd.read_csv("data/processed/customers.csv")
        assert not customers.empty, "Customers dataframe is empty"
        assert customers["customer_id"].is_unique, "customer_id is not unique"
        assert (customers["account_balance"] >= 0).all(), "Negative account balances found"
        print("[PASSED] TEST 2: Customer profiles unique and valid.")
        passed += 1
    except Exception as e:
        print(f"[FAILED] TEST 2: {e}")
        failed += 1

    # Test 3: Transaction Amounts Positive (Silver Quality Gate Check)
    try:
        transactions = pd.read_parquet("data/silver/transactions")
        assert not transactions.empty, "Silver transactions dataframe is empty"
        assert (transactions["amount"] > 0).all(), "Non-positive transaction amounts found in Silver layer"
        print("[PASSED] TEST 3: Silver transaction quality gate verified (100% positive amounts).")
        passed += 1
    except Exception as e:
        print(f"[FAILED] TEST 3: {e}")
        failed += 1

    # Test 4: Gold ML Analytics Parquet Output
    try:
        gold_ml_path = "data/gold/loan_risk_analytics"
        assert os.path.exists(gold_ml_path), "Gold loan risk analytics output missing"
        print("[PASSED] TEST 4: PySpark ML Gold analytics Parquet output verified.")
        passed += 1
    except Exception as e:
        print(f"[FAILED] TEST 4: {e}")
        failed += 1

    print("------------------------------------------")
    print(f"SUMMARY: {passed} PASSED, {failed} FAILED.")
    print("==========================================")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
