import urllib.request
import json
import logging
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_minio_buckets(endpoint="http://localhost:9000", access_key="minioadmin", secret_key="minioadmin"):
    """
    Provisions S3 buckets on MinIO S3 object storage server.
    """
    buckets = ["bank-lakehouse-raw", "bank-lakehouse-silver", "bank-lakehouse-gold"]
    
    try:
        import boto3
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=boto3.session.Config(signature_version='s3v4')
        )
        
        logger.info(f"Connected to MinIO S3 at {endpoint}")
        
        existing_buckets = [b['Name'] for b in s3_client.list_buckets().get('Buckets', [])]
        logger.info(f"Existing S3 buckets: {existing_buckets}")
        
        for bucket in buckets:
            if bucket not in existing_buckets:
                s3_client.create_bucket(Bucket=bucket)
                logger.info(f"✅ Created S3 bucket: {bucket}")
            else:
                logger.info(f"ℹ️ S3 bucket already exists: {bucket}")
                
        return True
        
    except ImportError:
        logger.warning("boto3 not installed. Creating local directory fallback for MinIO S3 buckets.")
        for bucket in buckets:
            local_bucket_dir = f"data/minio/{bucket}"
            os.makedirs(local_bucket_dir, exist_ok=True)
            logger.info(f"📁 Local bucket fallback directory ready: {local_bucket_dir}")
        return True
    except Exception as e:
        logger.warning(f"⚠️ MinIO S3 not running at {endpoint} ({str(e)}). Local fallback directories ready.")
        for bucket in buckets:
            local_bucket_dir = f"data/minio/{bucket}"
            os.makedirs(local_bucket_dir, exist_ok=True)
        return False

if __name__ == "__main__":
    setup_minio_buckets()
