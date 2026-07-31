from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
import sys
import os

# Add config to path
sys.path.append('/opt/airflow/spark_jobs/config')
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config'))
from spark_config import create_spark_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_bronze_to_silver():
    """Process raw data to silver layer - UPDATED for Kaggle data structure"""
    spark = create_spark_session("BronzeToSilver")
    
    try:
        # Determine base path depending on environment (Docker container vs local test)
        base_path = "/opt/airflow/data" if os.path.exists("/opt/airflow/data") else "data"
        
        # Read raw CSV files
        customers = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{base_path}/processed/customers.csv")
        transactions = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{base_path}/processed/transactions.csv")
        revenue = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{base_path}/processed/revenue.csv")
        costs = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{base_path}/processed/costs.csv")
        branches = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{base_path}/processed/branches.csv")
        loans = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{base_path}/processed/loans.csv")
        
        # Transform customers - UPDATED for Kaggle structure
        customers_silver = customers \
            .withColumn("age_group", 
                       when(col("age") < 25, "18-24")
                       .when(col("age") < 35, "25-34")
                       .when(col("age") < 45, "35-44")
                       .when(col("age") < 55, "45-54")
                       .when(col("age") < 65, "55-64")
                       .otherwise("65+")) \
            .withColumn("income_segment",
                       when(col("annual_income") < 300000, "Low")
                       .when(col("annual_income") < 800000, "Medium")
                       .otherwise("High")) \
            .withColumn("balance_segment",
                       when(col("account_balance") < 50000, "Low")
                       .when(col("account_balance") < 200000, "Medium")
                       .otherwise("High")) \
            .withColumn("updated_timestamp", current_timestamp())
        
        # Transform transactions - UPDATED for Kaggle structure
        transactions_silver = transactions \
            .withColumn("transaction_date", to_date(col("timestamp"))) \
            .withColumn("is_debit", col("transaction_type").isin(["WITHDRAWAL", "PAYMENT", "PURCHASE"])) \
            .withColumn("is_credit", col("transaction_type").isin(["DEPOSIT", "TRANSFER"])) \
            .withColumn("amount_category",
                       when(col("amount") < 500, "Small")
                       .when(col("amount") < 5000, "Medium")
                       .otherwise("Large")) \
            .withColumn("updated_timestamp", current_timestamp())
        
        # Transform revenue data
        revenue_silver = revenue \
            .withColumn("event_date", to_date(col("event_date"))) \
            .withColumn("updated_timestamp", current_timestamp())
        
        # Transform cost data
        costs_silver = costs \
            .withColumn("cost_date", to_date(col("cost_date"))) \
            .withColumn("updated_timestamp", current_timestamp())
        
        # Transform loan data
        loans_silver = loans \
            .withColumn("start_date", to_date(col("start_date"))) \
            .withColumn("updated_timestamp", current_timestamp())
        
        # Write to local storage (simulating Silver layer)
        customers_silver.write.mode("overwrite").parquet(f"{base_path}/silver/customers")
        transactions_silver.write.mode("overwrite").parquet(f"{base_path}/silver/transactions")
        revenue_silver.write.mode("overwrite").parquet(f"{base_path}/silver/revenue")
        costs_silver.write.mode("overwrite").parquet(f"{base_path}/silver/costs")
        loans_silver.write.mode("overwrite").parquet(f"{base_path}/silver/loans")
        
        logger.info("✅ Bronze to Silver processing completed with Kaggle data structure")
        
    except Exception as e:
        logger.error(f"❌ Error in Bronze to Silver: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    process_bronze_to_silver()
