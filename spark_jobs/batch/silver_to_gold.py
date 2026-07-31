from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
import sys
import os

# Add config to path
sys.path.append('/opt/airflow/spark_jobs/config')
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config'))
from spark_config import create_spark_session, get_postgres_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_kpis(spark):
    """Calculate financial KPIs - UPDATED for Kaggle data"""
    
    # Determine base path depending on environment
    base_path = "/opt/airflow/data" if os.path.exists("/opt/airflow/data") else "data"
    
    # Read silver data
    customers = spark.read.parquet(f"{base_path}/silver/customers")
    transactions = spark.read.parquet(f"{base_path}/silver/transactions")
    revenue = spark.read.parquet(f"{base_path}/silver/revenue")
    costs = spark.read.parquet(f"{base_path}/silver/costs")
    loans = spark.read.parquet(f"{base_path}/silver/loans")
    
    # Customer Profitability
    customer_revenue = revenue.groupBy("customer_id").agg(sum("amount").alias("total_revenue"))
    customer_transactions = transactions.groupBy("customer_id").agg(
        sum(when(col("is_credit"), col("amount")).otherwise(0)).alias("total_credits"),
        sum(when(col("is_debit"), col("amount")).otherwise(0)).alias("total_debits"),
        count("transaction_id").alias("transaction_count")
    )
    
    customer_profitability = (customers
        .join(customer_revenue, "customer_id", "left")
        .join(customer_transactions, "customer_id", "left")
        .withColumn("total_revenue", coalesce("total_revenue", lit(0)))
        .withColumn("estimated_costs", col("transaction_count") * 5)  # ₹5 per transaction
        .withColumn("net_profit", col("total_revenue") - col("estimated_costs"))
        .withColumn("profit_margin", 
                   when(col("total_revenue") > 0, col("net_profit") / col("total_revenue"))
                   .otherwise(0))
        .withColumn("kpi_date", current_date())
        .select("customer_id", "customer_segment", "total_revenue", "estimated_costs", 
               "net_profit", "profit_margin", "kpi_date"))
    
    # Branch Performance
    branch_revenue = revenue.groupBy("branch_id").agg(sum("amount").alias("total_revenue"))
    branch_costs = costs.groupBy("branch_id").agg(sum("amount").alias("total_costs"))
    branch_transactions = transactions.groupBy("branch_id").agg(count("transaction_id").alias("transaction_count"))
    
    branch_performance = (branch_revenue
        .join(branch_costs, "branch_id", "left")
        .join(branch_transactions, "branch_id", "left")
        .withColumn("total_costs", coalesce("total_costs", lit(0)))
        .withColumn("net_income", col("total_revenue") - col("total_costs"))
        .withColumn("cost_income_ratio",
                   when(col("total_revenue") > 0, col("total_costs") / col("total_revenue"))
                   .otherwise(0))
        .withColumn("transaction_per_staff", 
                   when(col("transaction_count") > 0, col("transaction_count") / 20)  # Assuming 20 staff per branch
                   .otherwise(0))
        .withColumn("kpi_date", current_date())
        .select("branch_id", "total_revenue", "total_costs", "net_income", 
               "cost_income_ratio", "transaction_count", "transaction_per_staff", "kpi_date"))
    
    # Loan Portfolio Analysis
    loan_portfolio = (loans
        .filter(col("status") == "ACTIVE")
        .groupBy("branch_id")
        .agg(
            sum("loan_amount").alias("total_loan_portfolio"),
            sum("outstanding_balance").alias("total_outstanding"),
            avg("interest_rate").alias("avg_interest_rate"),
            count("loan_id").alias("active_loans")
        )
        .withColumn("kpi_date", current_date()))
    
    return customer_profitability, branch_performance, loan_portfolio

def write_to_postgres(spark, df, table_name):
    """Write DataFrame to PostgreSQL"""
    try:
        postgres_config = get_postgres_config()
        
        df.write \
            .format("jdbc") \
            .option("url", postgres_config["url"]) \
            .option("dbtable", f"bank_dwh.{table_name}") \
            .option("user", postgres_config["user"]) \
            .option("password", postgres_config["password"]) \
            .option("driver", postgres_config["driver"]) \
            .option("truncate", "true") \
            .mode("overwrite") \
            .save()
        
        logger.info(f"✅ Successfully wrote {table_name} to PostgreSQL")
        
    except Exception as e:
        logger.error(f"❌ Error writing to PostgreSQL: {str(e)}")
        # Fallback to local Parquet write
        base_path = "/opt/airflow/data" if os.path.exists("/opt/airflow/data") else "data"
        df.write.mode("overwrite").parquet(f"{base_path}/gold/{table_name}")

def process_silver_to_gold():
    """Process silver data to gold layer and load to PostgreSQL - UPDATED for Kaggle"""
    spark = create_spark_session("SilverToGold")
    
    try:
        # Add ML module path
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml'))
        from loan_default_predictor import train_and_predict_loan_defaults

        # Calculate KPIs
        customer_profitability, branch_performance, loan_portfolio = calculate_kpis(spark)
        
        # Write to PostgreSQL
        write_to_postgres(spark, customer_profitability, "customer_profitability")
        write_to_postgres(spark, branch_performance, "branch_performance")
        write_to_postgres(spark, loan_portfolio, "loan_portfolio")
        
        # Also save locally
        base_path = "/opt/airflow/data" if os.path.exists("/opt/airflow/data") else "data"
        customer_profitability.write.mode("overwrite").parquet(f"{base_path}/gold/customer_profitability")
        branch_performance.write.mode("overwrite").parquet(f"{base_path}/gold/branch_performance")
        loan_portfolio.write.mode("overwrite").parquet(f"{base_path}/gold/loan_portfolio")

        # Run PySpark ML Loan Default Prediction Engine
        try:
            loan_risk_analytics = train_and_predict_loan_defaults(spark, base_path)
            if loan_risk_analytics is not None:
                write_to_postgres(spark, loan_risk_analytics, "loan_risk_analytics")
        except Exception as ml_err:
            logger.warning(f"⚠️ ML Prediction skipped or encountered warning: {str(ml_err)}")
        
        logger.info("✅ Silver to Gold processing completed with Kaggle data & ML Predictive Risk Engine")
        
    except Exception as e:
        logger.error(f"❌ Error in Silver to Gold: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    process_silver_to_gold()
