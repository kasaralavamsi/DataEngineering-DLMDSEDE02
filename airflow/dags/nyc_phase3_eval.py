from datetime import datetime
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.empty import EmptyOperator

BRONZE_BASE = "hdfs://namenode:9000/datalake/nyc/bronze"
SILVER_BASE = "hdfs://namenode:9000/datalake/nyc/silver"
GOLD_BASE = "hdfs://namenode:9000/datalake/nyc/gold"
POSTGRES_JDBC = "jdbc:postgresql://postgres:5432/nyc"

with DAG(
    dag_id="nyc_phase3_eval",
    start_date=datetime(2023,1,1),
    schedule=None,
    catchup=False,
    default_args={"owner": "you"},
    tags=["nyc","phase3","evaluation"],
) as dag:

    start = EmptyOperator(task_id="start")

    dq_silver = SparkSubmitOperator(
        task_id="dq_check_silver",
        application="/opt/airflow/spark_jobs/dq_check_silver.py",
        application_args=["--silver_base", SILVER_BASE, "--jdbc_url", POSTGRES_JDBC, "--jdbc_user", "nyc", "--jdbc_password", "nyc"],
        packages="org.postgresql:postgresql:42.7.3",
        conf={"spark.master": "spark://spark-master:7077"}
    )

    eval_gold = SparkSubmitOperator(
        task_id="evaluate_gold_metrics",
        application="/opt/airflow/spark_jobs/evaluate_gold_metrics.py",
        application_args=["--gold_base", GOLD_BASE, "--jdbc_url", POSTGRES_JDBC, "--jdbc_user", "nyc", "--jdbc_password", "nyc"],
        packages="org.postgresql:postgresql:42.7.3",
        conf={"spark.master": "spark://spark-master:7077"}
    )

    end = EmptyOperator(task_id="end")

    start >> dq_silver >> eval_gold >> end
