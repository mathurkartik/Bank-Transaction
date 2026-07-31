from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, sum as _sum, count as _count, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
import logging
import sys
import os

sys.path.append('/opt/airflow/spark_jobs/config')
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config'))
from spark_config import create_spark_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def consume_kafka_stream(bootstrap_servers="localhost:9092", topic="bank.transactions.v1"):
    """
    Consumes live transaction stream from Kafka using Spark Structured Streaming,
    applies watermarking and sliding window aggregations, and prints results.
    """
    spark = create_spark_session("KafkaStreamConsumer")

    # Define schema matching producer payload
    schema = StructType([
        StructField("transaction_id", StringType()),
        StructField("customer_id", StringType()),
        StructField("branch_id", StringType()),
        StructField("amount", DoubleType()),
        StructField("transaction_type", StringType()),
        StructField("timestamp", StringType())
    ])

    try:
        # Read stream from Kafka
        kafka_stream = spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", bootstrap_servers) \
            .option("subscribe", topic) \
            .option("startingOffsets", "latest") \
            .load()

        # Parse JSON and parse event timestamp
        parsed_df = kafka_stream \
            .selectExpr("CAST(value AS STRING) as json_payload") \
            .select(from_json(col("json_payload"), schema).alias("data")) \
            .select("data.*") \
            .withColumn("event_time", col("timestamp").cast(TimestampType()))

        # Watermarking & 5-minute sliding window aggregations
        windowed_agg = parsed_df \
            .withWatermark("event_time", "10 minutes") \
            .groupBy(
                window(col("event_time"), "5 minutes", "1 minute"),
                col("branch_id")
            ) \
            .agg(
                _sum("amount").alias("window_total_volume"),
                _count("transaction_id").alias("window_txn_count")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("branch_id"),
                col("window_total_volume"),
                col("window_txn_count")
            )

        logger.info(f"⚡ Spark Structured Streaming active on topic '{topic}'...")

        # Write to console in complete/update mode
        query = windowed_agg.writeStream \
            .outputMode("update") \
            .format("console") \
            .option("truncate", "false") \
            .start()

        query.awaitTermination()

    except Exception as e:
        logger.error(f"❌ Error in Spark Structured Streaming Consumer: {str(e)}")
    finally:
        spark.stop()

if __name__ == "__main__":
    consume_kafka_stream()
