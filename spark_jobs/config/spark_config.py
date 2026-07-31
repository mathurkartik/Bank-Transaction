from pyspark.sql import SparkSession
import logging
import os

logger = logging.getLogger(__name__)

def create_spark_session(app_name):
    """Create Spark session configured for MinIO S3A object storage & Iceberg"""
    s3_endpoint = "http://minio:9000" if os.path.exists("/opt/airflow") else "http://localhost:9000"
    
    try:
        spark = SparkSession.builder \
            .appName(app_name) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .config("spark.sql.parquet.compression.codec", "snappy") \
            .config("spark.jars.packages", "org.postgresql:postgresql:42.5.4,org.apache.hadoop:hadoop-aws:3.3.4") \
            .config("spark.hadoop.fs.s3a.endpoint", s3_endpoint) \
            .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
            .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
            .config("spark.hadoop.fs.s3a.path.style.access", "true") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
            .config("spark.sql.catalog.local_iceberg", "org.apache.iceberg.spark.SparkCatalog") \
            .config("spark.sql.catalog.local_iceberg.type", "hadoop") \
            .config("spark.sql.catalog.local_iceberg.warehouse", "data/iceberg_warehouse") \
            .master("local[*]") \
            .getOrCreate()
        
        logger.info(f"Spark session created for {app_name} with S3A MinIO support")
        return spark
        
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}")
        raise

def get_postgres_config():
    """Get PostgreSQL connection configuration dynamically based on environment"""
    host = "postgres-warehouse" if os.path.exists("/opt/airflow") else "localhost"
    return {
        "url": f"jdbc:postgresql://{host}:5432/bank_warehouse",
        "user": "airflow",
        "password": "airflow",
        "driver": "org.postgresql.Driver"
    }
