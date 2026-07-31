from pyspark.sql import SparkSession
import logging

logger = logging.getLogger(__name__)

def create_spark_session(app_name):
    """Create local Spark session"""
    try:
        spark = SparkSession.builder \
            .appName(app_name) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .config("spark.sql.parquet.compression.codec", "snappy") \
            .config("spark.jars.packages", "org.postgresql:postgresql:42.5.4") \
            .master("local[*]") \
            .getOrCreate()
        
        logger.info(f"Spark session created for {app_name}")
        return spark
        
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}")
        raise

def get_postgres_config():
    """Get PostgreSQL connection configuration"""
    return {
        "url": "jdbc:postgresql://postgres-warehouse:5432/bank_warehouse",
        "user": "airflow",
        "password": "airflow",
        "driver": "org.postgresql.Driver"
    }
