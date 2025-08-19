# airflow/dags/spark_load_taxi.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "you",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="load_taxi_zone_lookup_daily",
    default_args=default_args,
    start_date=datetime(2025, 8, 1),
    schedule_interval="0 2 * * *",  # daily at 02:00
    catchup=False,
    tags=["nyc", "batch"],
) as dag:

    spark_submit = BashOperator(
        task_id="spark_submit",
        bash_command="/spark/bin/spark-submit \
            --master spark://spark-master:7077 \
            --packages org.postgresql:postgresql:42.6.0 \
            /opt/spark/jobs/load_taxi_zone.py",
    )

    spark_submit
