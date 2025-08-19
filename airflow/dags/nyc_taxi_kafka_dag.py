from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
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

def download_and_produce(**context):
    import sys
    sys.path.append("/opt/airflow/scripts")
    from download_nyc_tlc import download_month
    from kafka_producer import produce_parquet_to_kafka
    year = int(context['params'].get('year', 2023))
    month = int(context['params'].get('month', 1))
    color = context['params'].get('color', 'yellow')
    local_path = download_month(RAW_DIR, year, month, color)
    produce_parquet_to_kafka(local_path, bootstrap="kafka:9092", topic="trips_raw", limit=40000)

with DAG(
    dag_id="nyc_taxi_kafka_batch",
    start_date=datetime(2023, 1, 1),
    schedule=None,
    catchup=False,
    default_args={"owner": "you"},
    params={"year": Param(2023, type="integer"), "month": Param(1, type="integer"), "color": Param("yellow", enum=["yellow","green","fhv"]) },
    tags=["nyc","kafka","batch"],
) as dag:

    t0 = PythonOperator(task_id="prepare_dirs", python_callable=ensure_dirs)
    t1 = PythonOperator(task_id="download_and_produce", python_callable=download_and_produce)

    spark_kafka_bronze = SparkSubmitOperator(
        task_id="spark_kafka_to_bronze",
        application="/opt/airflow/spark_jobs/spark_kafka_to_bronze_batch.py",
        application_args=["--bootstrap","kafka:9092","--topic","trips_raw","--bronze_base",BRONZE_BASE,"--startingOffsets","earliest","--endingOffsets","latest"],
        packages="org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0",
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

    t0 >> t1 >> spark_kafka_bronze >> spark_silver >> spark_gold
