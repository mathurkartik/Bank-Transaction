from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, when, expr, current_timestamp, rand, lit
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import LogisticRegression
from pyspark.ml import Pipeline
import logging
import sys
import os

# Add config path
sys.path.append('/opt/airflow/spark_jobs/config')
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config'))
from spark_config import create_spark_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_and_predict_loan_defaults(spark: SparkSession = None, base_path: str = "data") -> DataFrame:
    """
    Trains a PySpark MLlib Logistic Regression model on loan and customer data
    to predict default probabilities and assign risk ratings.
    """
    should_stop_spark = False
    if spark is None:
        spark = create_spark_session("LoanDefaultPredictor")
        should_stop_spark = True

    try:
        loans_path = f"{base_path}/silver/loans"
        customers_path = f"{base_path}/silver/customers"

        if not os.path.exists(loans_path) or not os.path.exists(customers_path):
            logger.warning(f"Silver loans or customers path does not exist in {base_path}. Skipping ML prediction.")
            return None

        loans_df = spark.read.parquet(loans_path)
        customers_df = spark.read.parquet(customers_path)

        # Merge loans with customer demographics
        joined_df = loans_df.join(customers_df, "customer_id", "inner")

        # Fill missing values and ensure numeric columns exist
        ml_df = joined_df \
            .withColumn("outstanding_balance", col("outstanding_balance").cast("double")) \
            .withColumn("interest_rate", col("interest_rate").cast("double")) \
            .withColumn("account_balance", col("account_balance").cast("double")) \
            .withColumn("annual_income", col("annual_income").cast("double")) \
            .withColumn("loan_to_income_ratio", when(col("annual_income") > 0, col("outstanding_balance") / col("annual_income")).otherwise(0.5)) \
            .fillna(0.0)

        # Generate ground truth label for training if missing (simulating historical default indicator)
        if "is_default" not in ml_df.columns:
            ml_df = ml_df.withColumn("is_default", 
                when((col("loan_to_income_ratio") > 0.8) & (col("interest_rate") > 12.0), 1)
                .when(col("outstanding_balance") > 1000000, 1)
                .otherwise(0)
            )

        # Build MLlib Pipeline
        assembler = VectorAssembler(
            inputCols=["outstanding_balance", "interest_rate", "account_balance", "annual_income", "loan_to_income_ratio"],
            outputCol="features"
        )

        lr = LogisticRegression(featuresCol="features", labelCol="is_default", maxIter=10)
        pipeline = Pipeline(stages=[assembler, lr])

        # Fit model and transform data
        model = pipeline.fit(ml_df)
        predictions = model.transform(ml_df)

        # Extract probability of default (class 1)
        # Vector probability is [prob_0, prob_1], so we use expression to get prob_1
        get_prob_1 = expr("vector_to_array(probability)[1]")

        scored_df = predictions \
            .withColumn("default_probability", get_prob_1) \
            .withColumn("risk_rating",
                       when(col("default_probability") < 0.25, "Low")
                       .when(col("default_probability") < 0.55, "Moderate")
                       .when(col("default_probability") < 0.80, "High")
                       .otherwise("Critical")) \
            .withColumn("ml_evaluated_at", current_timestamp())

        # Select relevant analytics output columns
        output_df = scored_df.select(
            "loan_id", "customer_id", "branch_id", "loan_type",
            "outstanding_balance", "interest_rate", "annual_income",
            "loan_to_income_ratio", "default_probability", "risk_rating",
            "ml_evaluated_at"
        )

        # Save to Gold layer
        output_path = f"{base_path}/gold/loan_risk_analytics"
        output_df.write.mode("overwrite").parquet(output_path)
        logger.info(f"✅ ML Loan Default Prediction complete. Saved results to {output_path}")

        return output_df

    except Exception as e:
        logger.error(f"❌ Error in train_and_predict_loan_defaults: {str(e)}")
        raise
    finally:
        if should_stop_spark:
            spark.stop()

if __name__ == "__main__":
    train_and_predict_loan_defaults()
