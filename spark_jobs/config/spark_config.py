from pyspark.sql import SparkSession
import logging
import os

logger = logging.getLogger(__name__)

def create_spark_session(app_name):
    """Create Spark session configured for local execution with optional MinIO/Postgres support"""
    try:
        builder = SparkSession.builder \
            .appName(app_name) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .config("spark.sql.parquet.compression.codec", "snappy") \
            .master("local[*]")
        
        # Add S3A/Postgres configs if running in Docker container
        if os.path.exists("/opt/airflow"):
            builder = builder \
                .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
                .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
                .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
                .config("spark.hadoop.fs.s3a.path.style.access", "true")
            
        spark = builder.getOrCreate()
        logger.info(f"Spark session created for {app_name}")
        return spark
        
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}")
        return SparkSession.builder.appName(app_name).master("local[*]").getOrCreate()

def get_postgres_config():
    """Get PostgreSQL connection configuration dynamically based on environment"""
    host = "postgres-warehouse" if os.path.exists("/opt/airflow") else "localhost"
    return {
        "url": f"jdbc:postgresql://{host}:5432/bank_warehouse",
        "user": "airflow",
        "password": "airflow",
        "driver": "org.postgresql.Driver"
    }
