from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
import subprocess
import sys
import os

default_args = {
    'owner': 'bank_analytics',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'financial_analytics_pipeline',
    default_args=default_args,
    description='Bank Financial Analytics Pipeline',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['banking', 'analytics']
)

def run_data_integration():
    """Run data integration script"""
    try:
        cmd = ["python", "/opt/airflow/scripts/integrate_kaggle_synthetic.py"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/opt/airflow")
        
        if result.returncode != 0:
            print(f"Data integration output: {result.stdout}")
            print(f"Data integration error: {result.stderr}")
            raise Exception(f"Data integration failed")
        
        print("✅ Data integration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in data integration: {str(e)}")
        raise

def run_spark_job(job_name):
    """Run Spark job"""
    try:
        if job_name == "bronze_to_silver":
            script_path = "/opt/airflow/spark_jobs/batch/bronze_to_silver.py"
        elif job_name == "silver_to_gold":
            script_path = "/opt/airflow/spark_jobs/batch/silver_to_gold.py"
        else:
            raise ValueError(f"Unknown job: {job_name}")
        
        cmd = ["python", script_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/opt/airflow")
        
        if result.returncode != 0:
            print(f"Spark job {job_name} output: {result.stdout}")
            print(f"Spark job {job_name} error: {result.stderr}")
            raise Exception(f"Spark job {job_name} failed")
        
        print(f"✅ Spark job {job_name} completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error running Spark job {job_name}: {str(e)}")
        raise

# Define tasks
start_pipeline = EmptyOperator(task_id='start_pipeline', dag=dag)

integrate_data = PythonOperator(
    task_id='integrate_data',
    python_callable=run_data_integration,
    dag=dag,
)

bronze_to_silver = PythonOperator(
    task_id='bronze_to_silver',
    python_callable=run_spark_job,
    op_kwargs={'job_name': 'bronze_to_silver'},
    dag=dag,
)

silver_to_gold = PythonOperator(
    task_id='silver_to_gold',
    python_callable=run_spark_job,
    op_kwargs={'job_name': 'silver_to_gold'},
    dag=dag,
)

end_pipeline = EmptyOperator(task_id='end_pipeline', dag=dag)

# Define workflow
# You can toggle the comments below to include the data integration step in Airflow
# start_pipeline >> integrate_data >> bronze_to_silver >> silver_to_gold >> end_pipeline
start_pipeline >> bronze_to_silver >> silver_to_gold >> end_pipeline
