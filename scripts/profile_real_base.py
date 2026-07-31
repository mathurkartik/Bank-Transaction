import pandas as pd
import os
import sys

def profile_real_base(file_path="data/raw/bank_transactions.csv"):
    """
    Profiles ONLY the genuine, un-derived Kaggle raw base CSV dataset.
    Reports real fields and computes strict real-data ground-truth metrics.
    """
    if not os.path.exists(file_path):
        print(f"Error: Raw Kaggle dataset not found at {file_path}")
        sys.exit(1)

    print("==========================================================")
    print("[REAL DATA] REAL KAGGLE BASE DATASET PROFILING (UN-DERIVED FIELDS)")
    print("==========================================================")

    # Read raw CSV
    df = pd.read_csv(file_path, low_memory=False)
    total_records = len(df)
    
    print(f"\n1. GENUINE REAL FIELDS IN BASE CSV ({len(df.columns)} fields):")
    for col in df.columns:
        non_nulls = df[col].notna().sum()
        pct = (non_nulls / total_records) * 100
        print(f"   - {col}: {non_nulls:,} non-null values ({pct:.2f}%)")

    # Compute 2 honest descriptive metrics grounded STRICTLY in real fields
    total_amount = pd.to_numeric(df['TransactionAmount (INR)'], errors='coerce').sum()
    mean_amount = pd.to_numeric(df['TransactionAmount (INR)'], errors='coerce').mean()
    median_amount = pd.to_numeric(df['TransactionAmount (INR)'], errors='coerce').median()
    unique_cust = df['CustomerID'].nunique()
    
    print("\n2. GROUND-TRUTH DESCRIPTIVE STATISTICS [REAL KAGGLE BASE]:")
    print(f"   - Total Raw Record Count: {total_records:,} rows [REAL]")
    print(f"   - Unique Customer IDs: {unique_cust:,} [REAL]")
    print(f"   - Aggregate Real Transaction Amount: INR {total_amount:,.2f} [REAL]")
    print(f"   - Mean Real Transaction Amount: INR {mean_amount:,.2f} [REAL]")
    print(f"   - Median Real Transaction Amount: INR {median_amount:,.2f} [REAL]")

    print("\n==========================================================")
    return {
        "total_records": total_records,
        "unique_cust": unique_cust,
        "total_amount": total_amount,
        "mean_amount": mean_amount,
        "median_amount": median_amount
    }

if __name__ == "__main__":
    profile_real_base()
