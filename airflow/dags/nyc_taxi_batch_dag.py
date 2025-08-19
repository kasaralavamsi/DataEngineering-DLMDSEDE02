from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.models.baseoperator import chain
from airflow.models.param import Param
import os

DATA_DIR = "/opt/airflow/data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
BRONZE_BASE = "hdfs://namenode:9000/datalake/nyc/bronze"
SILVER_BASE = "hdfs://namenode:9000/datalake/nyc/silver"
GOLD_BASE = "hdfs://namenode:9000/datalake/nyc/gold"
POSTGRES_JDBC = "jdbc:postgresql://postgres:5432/nyc"

def ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)

def download_parametrized(**context):
    import sys
    sys.path.append("/opt/airflow/scripts")
    from download_nyc_tlc import download_month
    year = int(context['params'].get('year', 2023))
    month = int(context['params'].get('month', 1))
    color = context['params'].get('color', 'yellow')
    local_path = download_month(RAW_DIR, year, month, color)
    context['ti'].xcom_push(key='local_file', value=local_path)

with DAG(
    dag_id="nyc_taxi_batch",
    start_date=datetime(2023, 1, 1),
    schedule="@monthly",
    catchup=False,
    default_args={"owner": "you"},
    params={"year": Param(2023, type="integer"), "month": Param(1, type="integer"), "color": Param("yellow", enum=["yellow","green","fhv"]) },
    tags=["nyc","batch"],
) as dag:

    t0 = PythonOperator(task_id="prepare_dirs", python_callable=ensure_dirs)
    t1 = PythonOperator(task_id="download_dataset", python_callable=download_parametrized)

    spark_bronze = SparkSubmitOperator(
        task_id="spark_bronze",
        application="/opt/airflow/spark_jobs/nyc_bronze_to_silver.py",
        application_args=["--stage","bronze","--input","{{ ti.xcom_pull(task_ids='download_dataset', key='local_file') }}","--bronze_base",BRONZE_BASE],
        conf={"spark.master": "spark://spark-master:7077"}
    )

    spark_silver = SparkSubmitOperator(
        task_id="spark_silver",
        application="/opt/airflow/spark_jobs/nyc_bronze_to_silver.py",
        application_args=["--stage","silver","--bronze_base",BRONZE_BASE,"--silver_base",SILVER_BASE],
        conf={"spark.master": "spark://spark-master:7077"}
    )

    spark_gold = SparkSubmitOperator(
        task_id="spark_gold",
        application="/opt/airflow/spark_jobs/nyc_silver_to_gold.py",
        application_args=["--silver_base",SILVER_BASE,"--gold_base",GOLD_BASE,"--jdbc_url",POSTGRES_JDBC,"--jdbc_user","nyc","--jdbc_password","nyc"],
        packages="org.postgresql:postgresql:42.7.3",
        conf={"spark.master": "spark://spark-master:7077"}
    )

    chain(t0, t1, spark_bronze, spark_silver, spark_gold)
