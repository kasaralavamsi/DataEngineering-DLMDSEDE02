# Code Review Report – DLMDSEDE02 Phase 3

**Reviewed:** February 7, 2026
**Project:** NYC TLC Taxi Data Pipeline (Batch + Kafka + Medallion Architecture)

---

## CRITICAL Issues

### 1. Missing Docker Services: Kafka, Airflow, Superset
**Files:** `docker-compose.yml`, `README.md`
The README and DAGs reference **Apache Kafka**, **Apache Airflow**, and **Apache Superset** as core services, but **none of them are defined** in `docker-compose.yml`. The compose file only has: namenode, datanode, postgres, adminer, spark-master, spark-worker-1, spark-history, and hdfs-bootstrap.

**Impact:** The Kafka-based DAG (`nyc_taxi_kafka_dag.py`) cannot run. Airflow DAGs have no host. Superset dashboards cannot be accessed. The `verify.sh` script checks for kafka, zookeeper, and airflow-webserver containers that do not exist.

**Fix needed:** Add Kafka (+ Zookeeper), Airflow (webserver + scheduler), and Superset service definitions to `docker-compose.yml`.

### 2. HDFS Path Mismatch in `load_taxi_zone.py`
**File:** `app/load_taxi_zone.py` (line 9)
Reads from `hdfs://namenode:9000/datasets/taxi_zone_lookup.csv`, but the `hdfs-bootstrap` container puts files into `/data/raw/`, not `/datasets/`. The namenode only mounts `./datasets:/datasets:ro` as a local volume — it does NOT create an HDFS `/datasets` directory.

**Impact:** `load_taxi_zone.py` will fail with FileNotFoundException at runtime.

**Fix needed:** Change the HDFS path to `hdfs://namenode:9000/data/raw/taxi_zone_lookup.csv`.

### 3. Spark Job Path Mismatch in `spark_load_taxi.py` DAG
**File:** `airflow/dags/spark_load_taxi.py` (line 26)
References `/opt/spark/jobs/load_taxi_zone.py` but the docker-compose mounts `./app` to `/opt/spark/app` (not `/opt/spark/jobs`). The actual file path would be `/opt/spark/app/load_taxi_zone.py`.

**Impact:** DAG task `spark_submit` will fail — file not found.

**Fix needed:** Change path to `/opt/spark/app/load_taxi_zone.py`.

---

## WARNING Issues

### 4. Spark-Kafka Version Mismatch
**File:** `airflow/dags/nyc_taxi_kafka_dag.py` (line 46)
Uses package `org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0`, but the Spark cluster runs version **3.1.2**. This can cause `NoSuchMethodError` or similar runtime exceptions.

**Fix needed:** Change to `org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2`.

### 5. No CREATE TABLE for Several PostgreSQL Tables
**Files:** `sql/init_postgres.sql`, `sql/init_phase3_metrics.sql`
Only `batch_clean` and `job_runs` tables are pre-created. The Spark jobs write to `fact_trips_monthly`, `dq_results`, `metrics_pipeline_runs`, and `taxi_zone_lookup` using `mode("overwrite")` or `mode("append")` — Spark JDBC auto-creates these tables, but without proper constraints, indexes, or data types.

**Impact:** No primary keys, no indexes, no proper data types (Spark defaults to TEXT-heavy schemas). Superset queries may be slow on large datasets.

**Recommendation:** Add explicit CREATE TABLE statements to the SQL init scripts for all 6 tables with proper types, PKs, and indexes.

### 6. Missing Python Dependencies in Containers
**File:** `scripts/kafka_producer.py`
Uses `kafka-python` and `pandas` libraries, which are imported at runtime inside the Airflow DAG. These libraries may not be installed in the Airflow container unless explicitly included in a Dockerfile or requirements.

**File:** `airflow/requirements.txt`
Only has `apache-airflow-providers-postgres` and `psycopg2-binary`. Missing: `kafka-python`, `pandas`, `pyarrow`, `apache-airflow-providers-apache-spark`.

### 7. No JDBC Driver JAR Configured for Standalone Spark Runs
**File:** `app/spark_job.py`
Uses JDBC PostgreSQL driver but does not specify `--packages` or `--jars` in the code. The `jars/postgresql-42.6.0.jar` exists in the repo but is not mounted into the Spark container or referenced in spark-submit commands within the compose file.

**Impact:** Running spark_job.py directly via `spark-submit` (as in the README instructions) will fail unless `--packages org.postgresql:postgresql:42.6.0` is passed — which the README does NOT include.

### 8. Hardcoded Credentials
**Files:** Multiple files
PostgreSQL credentials (`nyc`/`nyc`) are hardcoded throughout the codebase. While acceptable for a course project, this is a security concern for any production use.

---

## INFO / Minor Issues

### 9. `spark_job.py` AppName Says "Phase2"
**File:** `app/spark_job.py` (line 15)
The app name is `"Phase2BatchJob"` but this is a Phase 3 submission. Minor naming inconsistency.

### 10. No `.gitignore` File
The repository includes `.DS_Store` files and `__pycache__` directories. A `.gitignore` should exclude these.

### 11. `taxi_zone_lookup.csv` Directory is Empty
**File:** `taxi_zone_lookup.csv/` (this is a directory, not a file)
The compose file references `./taxi_zone_lookup.csv:/docker-entrypoint-initdb.d/taxi_zone_lookup.csv:ro` but `taxi_zone_lookup.csv` at the root is an empty directory. The actual CSV is at `datasets/taxi_zone_lookup.csv`.

**Impact:** PostgreSQL COPY command (if any) referencing this path would fail.

### 12. Event Log Configuration Without Directory
Spark services have `SPARK_EVENTLOG_ENABLED=true` and `SPARK_EVENTLOG_DIR=/tmp/spark-events` but the Spark History Server expects the directory to be populated. This works because of the shared `spark-events` volume, but could fail if the volume mount order changes.

---

## What IS Working Correctly

- **docker-compose.yml** core HDFS + Spark + PostgreSQL services are well-structured with health checks, proper dependency ordering, and shared volumes.
- **hdfs-bootstrap** service correctly initializes HDFS directories and uploads CSV files idempotently.
- **Medallion architecture** (Bronze → Silver → Gold) is properly implemented across the Spark jobs with correct partitioning by year/month.
- **Data quality checks** (`dq_check_silver.py`) implement meaningful null-rate and bad-value thresholds.
- **Pipeline evaluation** (`evaluate_gold_metrics.py`) provides good audit trail with run IDs and timestamps.
- **SQL initialization** scripts use `IF NOT EXISTS` for idempotent container restarts.
- **Airflow DAGs** have proper parameterization (year, month, color) with sensible defaults.
- **Kafka producer** handles datetime serialization correctly for JSON transport.
- **Download script** is idempotent (skips if file already exists).
- **E2E script** (`run_e2e.sh`) is well-structured with proper health-check waits.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 3     |
| Warning  | 5     |
| Info     | 4     |

The core ETL logic and medallion architecture are solid. The main gap is that **3 critical infrastructure services (Kafka, Airflow, Superset) are missing from docker-compose.yml**, and there are several path mismatches that would cause runtime failures. Adding the missing services and fixing the paths would make this pipeline fully operational.
