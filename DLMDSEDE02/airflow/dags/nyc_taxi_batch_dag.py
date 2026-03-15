from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.models.baseoperator import chain
from airflow.models.param import Param
import os

DATA_DIR  = "/opt/airflow/data"
RAW_DIR   = os.path.join(DATA_DIR, "raw")

# HDFS URIs used by Spark (hdfs://) and WebHDFS REST API (http://)
HDFS_RAW      = "hdfs://namenode:9000/datalake/nyc/raw"
HDFS_RAW_PATH = "/datalake/nyc/raw"      # path-only portion for WebHDFS calls
WEBHDFS_HOST  = "namenode"
WEBHDFS_PORT  = 9870

BRONZE_BASE   = "hdfs://namenode:9000/datalake/nyc/bronze"
SILVER_BASE   = "hdfs://namenode:9000/datalake/nyc/silver"
GOLD_BASE     = "hdfs://namenode:9000/datalake/nyc/gold"
POSTGRES_JDBC = "jdbc:postgresql://postgres:5432/nyc"


# ── WebHDFS helpers (no external binaries needed) ────────────────────────────

def _webhdfs_mkdirs(path, host=WEBHDFS_HOST, port=WEBHDFS_PORT):
    """Create an HDFS directory (and parents) via WebHDFS REST.

    HDFS permission checking is disabled via dfs.permissions.enabled=false in
    docker-compose, so any service user can write freely (dev/academic env).
    """
    import requests
    url = f"http://{host}:{port}/webhdfs/v1{path}?op=MKDIRS"
    r = requests.put(url)
    r.raise_for_status()
    print(f"HDFS mkdir {path}: {r.json()}")


def _webhdfs_put(local_path, hdfs_path, host=WEBHDFS_HOST, port=WEBHDFS_PORT):
    """Upload a local file to HDFS via WebHDFS two-step redirect protocol."""
    import requests
    # Step 1 – initiate; HDFS returns 307 redirect to the target DataNode
    url = f"http://{host}:{port}/webhdfs/v1{hdfs_path}?op=CREATE&overwrite=true"
    r = requests.put(url, allow_redirects=False)
    if r.status_code == 307:
        redirect_url = r.headers["Location"]
    elif r.status_code == 201:
        # Some configurations complete in one step
        return
    else:
        r.raise_for_status()

    # Step 2 – stream the file to the DataNode URL
    with open(local_path, "rb") as fh:
        r2 = requests.put(
            redirect_url,
            data=fh,
            headers={"Content-Type": "application/octet-stream"},
        )
    r2.raise_for_status()
    print(f"Uploaded {local_path} → {hdfs_path} ({r2.status_code})")


# ── Task callables ────────────────────────────────────────────────────────────

def ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)


def download_and_stage(**context):
    """Download TLC parquet locally, then stage it on HDFS raw zone.

    Spark executors run on worker nodes that do NOT share the Airflow
    scheduler's local filesystem.  Passing a ``file://`` path to
    SparkSubmitOperator always causes a FileNotFoundException on the
    executor side.  Uploading to HDFS first gives every Spark node
    uniform access via the ``hdfs://`` URI scheme.

    WebHDFS (port 9870) is used for the upload because the Spark 3.1.2
    binary distribution bundles Hadoop JARs but not the ``hdfs`` CLI.
    """
    import sys
    sys.path.append("/opt/airflow/scripts")
    from download_nyc_tlc import download_month

    year  = int(context["params"].get("year",  2023))
    month = int(context["params"].get("month", 1))
    color = context["params"].get("color", "yellow")

    # 1. Download locally (idempotent – skipped if file already exists)
    local_path = download_month(RAW_DIR, year, month, color)
    filename   = os.path.basename(local_path)

    # 2. Create HDFS raw directory
    _webhdfs_mkdirs(HDFS_RAW_PATH)

    # 3. Upload to HDFS (overwrite so re-runs are safe)
    hdfs_file_path = f"{HDFS_RAW_PATH}/{filename}"
    _webhdfs_put(local_path, hdfs_file_path)

    # 4. Push the full HDFS URI for spark_bronze
    hdfs_uri = f"{HDFS_RAW}/{filename}"
    context["ti"].xcom_push(key="hdfs_input", value=hdfs_uri)
    print(f"Staged → {hdfs_uri}")


# ── DAG definition ────────────────────────────────────────────────────────────

with DAG(
    dag_id="nyc_taxi_batch",
    start_date=datetime(2023, 1, 1),
    schedule="@monthly",
    catchup=False,
    default_args={"owner": "you"},
    params={
        "year":  Param(2023, type="integer"),
        "month": Param(1,    type="integer"),
        "color": Param("yellow", enum=["yellow", "green", "fhv"]),
    },
    tags=["nyc", "batch"],
) as dag:

    t0 = PythonOperator(task_id="prepare_dirs",    python_callable=ensure_dirs)
    t1 = PythonOperator(task_id="download_dataset", python_callable=download_and_stage)

    # Shared Spark config applied to every SparkSubmitOperator.
    # executor_memory=2g  — prevents disk-spill during the silver repartition
    #                        shuffle on a full monthly NYC taxi file (~3 M rows).
    # execution_timeout   — 2 h ceiling stops run-away jobs while being safely
    #                        above the expected ~40 min worst-case runtime.
    #                        Without this Airflow falls back to the global
    #                        default (None) so zombie detection is the only
    #                        kill mechanism.
    _SPARK_CONF = {"spark.master": "spark://spark-master:7077"}

    # spark_bronze reads the HDFS URI pushed by download_dataset so that
    # every Spark executor (on any worker node) can open it.
    spark_bronze = SparkSubmitOperator(
        task_id="spark_bronze",
        application="/opt/airflow/spark_jobs/nyc_bronze_to_silver.py",
        application_args=[
            "--stage",       "bronze",
            "--input",       "{{ ti.xcom_pull(task_ids='download_dataset', key='hdfs_input') }}",
            "--bronze_base", BRONZE_BASE,
        ],
        executor_memory="2g",
        conf=_SPARK_CONF,
        execution_timeout=timedelta(hours=2),
        retries=1,
        retry_delay=timedelta(minutes=2),
    )

    spark_silver = SparkSubmitOperator(
        task_id="spark_silver",
        application="/opt/airflow/spark_jobs/nyc_bronze_to_silver.py",
        application_args=[
            "--stage",       "silver",
            "--bronze_base", BRONZE_BASE,
            "--silver_base", SILVER_BASE,
        ],
        executor_memory="2g",
        conf=_SPARK_CONF,
        execution_timeout=timedelta(hours=2),
        retries=1,
        retry_delay=timedelta(minutes=2),
    )

    spark_gold = SparkSubmitOperator(
        task_id="spark_gold",
        application="/opt/airflow/spark_jobs/nyc_silver_to_gold.py",
        application_args=[
            "--silver_base",   SILVER_BASE,
            "--gold_base",     GOLD_BASE,
            "--jdbc_url",      POSTGRES_JDBC,
            "--jdbc_user",     "nyc",
            "--jdbc_password", "nyc",
        ],
        packages="org.postgresql:postgresql:42.7.3",
        executor_memory="2g",
        conf=_SPARK_CONF,
        execution_timeout=timedelta(hours=2),
        retries=1,
        retry_delay=timedelta(minutes=2),
    )

    chain(t0, t1, spark_bronze, spark_silver, spark_gold)
