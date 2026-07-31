import pandas as pd
import os

print("=== DATA INTEGRITY ANALYSIS ===")

# Load files
data_dir = "data/processed"
customers = pd.read_csv(f"{data_dir}/customers.csv")
transactions = pd.read_csv(f"{data_dir}/transactions.csv")
revenue = pd.read_csv(f"{data_dir}/revenue.csv")
costs = pd.read_csv(f"{data_dir}/costs.csv")
loans = pd.read_csv(f"{data_dir}/loans.csv")
branches = pd.read_csv(f"{data_dir}/branches.csv")

# 1. Check duplicate rows (exactly identical rows)
print("\n1. Duplicate Rows Check:")
print(f"   - Customers duplicates: {customers.duplicated().sum()}")
print(f"   - Transactions duplicates: {transactions.duplicated().sum()}")
print(f"   - Revenue duplicates: {revenue.duplicated().sum()}")
print(f"   - Costs duplicates: {costs.duplicated().sum()}")
print(f"   - Loans duplicates: {loans.duplicated().sum()}")
print(f"   - Branches duplicates: {branches.duplicated().sum()}")

# 2. Check Primary Key uniqueness
print("\n2. Primary Key Uniqueness Check:")
print(f"   - customers (customer_id) is unique: {customers['customer_id'].is_unique} ({customers['customer_id'].nunique()} unique)")
print(f"   - transactions (transaction_id) is unique: {transactions['transaction_id'].is_unique} ({transactions['transaction_id'].nunique()} unique)")
print(f"   - revenue (revenue_id) is unique: {revenue['revenue_id'].is_unique} ({revenue['revenue_id'].nunique()} unique)")
print(f"   - costs (cost_id) is unique: {costs['cost_id'].is_unique} ({costs['cost_id'].nunique()} unique)")
print(f"   - loans (loan_id) is unique: {loans['loan_id'].is_unique} ({loans['loan_id'].nunique()} unique)")
print(f"   - branches (branch_id) is unique: {branches['branch_id'].is_unique} ({branches['branch_id'].nunique()} unique)")

# 3. Referential Integrity Check (Relationships between files)
print("\n3. Referential Integrity (Foreign Key) Check:")
invalid_txn_cust = transactions[~transactions["customer_id"].isin(customers["customer_id"])]
print(f"   - Transaction customer_ids not in customers: {len(invalid_txn_cust)}")

invalid_rev_cust = revenue[~revenue["customer_id"].isin(customers["customer_id"])]
print(f"   - Revenue customer_ids not in customers: {len(invalid_rev_cust)}")

invalid_loan_cust = loans[~loans["customer_id"].isin(customers["customer_id"])]
print(f"   - Loan customer_ids not in customers: {len(invalid_loan_cust)}")

# Branch checks
branch_ids = branches["branch_id"].unique()
invalid_txn_branch = transactions[~transactions["branch_id"].isin(branch_ids)]
print(f"   - Transaction branch_ids not in branches: {len(invalid_txn_branch)}")

invalid_rev_branch = revenue[~revenue["branch_id"].isin(branch_ids)]
print(f"   - Revenue branch_ids not in branches: {len(invalid_rev_branch)}")

invalid_loan_branch = loans[~loans["branch_id"].isin(branch_ids)]
print(f"   - Loan branch_ids not in branches: {len(invalid_loan_branch)}")

# 4. Origin from Kaggle bank_transactions.csv
print("\n4. Kaggle Source File Origin Verification:")
kaggle_raw = pd.read_csv("data/raw/bank_transactions.csv", nrows=1000)
raw_cust_ids = "KAGGLE_" + kaggle_raw["CustomerID"].astype(str)
overlap = customers[customers["customer_id"].isin(raw_cust_ids)]
print(f"   - Customers originally matching Kaggle IDs: {len(overlap)} of {len(customers)}")
