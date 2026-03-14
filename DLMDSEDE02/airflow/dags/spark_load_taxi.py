# airflow/dags/spark_load_taxi.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

default_args = {
    "owner": "you",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

POSTGRES_JDBC = "jdbc:postgresql://postgres:5432/nyc"

with DAG(
    dag_id="load_taxi_zone_lookup_daily",
    default_args=default_args,
    start_date=datetime(2025, 8, 1),
    schedule_interval="0 2 * * *",  # daily at 02:00
    catchup=False,
    tags=["nyc", "batch"],
) as dag:

    # Downloads the TLC zone CSV and upserts into public.taxi_zone_lookup.
    # Script lives at /opt/airflow/spark_jobs/ (bind-mounted from ./airflow/spark_jobs/).
    # Previously used BashOperator with /spark/bin/spark-submit which does not
    # exist; Spark is installed at /opt/spark in the custom Airflow image.
    spark_submit = SparkSubmitOperator(
        task_id="spark_submit",
        application="/opt/airflow/spark_jobs/load_taxi_zone.py",
        packages="org.postgresql:postgresql:42.6.0",
        application_args=[
            "--jdbc_url",      POSTGRES_JDBC,
            "--jdbc_user",     "nyc",
            "--jdbc_password", "nyc",
        ],
        conf={"spark.master": "spark://spark-master:7077"},
        retries=1,
        retry_delay=timedelta(minutes=2),
    )

    spark_submit
