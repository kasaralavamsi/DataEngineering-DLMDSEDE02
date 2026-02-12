# DLMDSEDE02 — Data Engineering: Batch-Processing Data Architecture

> **IU International University of Applied Sciences**
> MSc Data Science — DLMDSEDE02 (Data Engineering)
> **Author:** Vamshi Krishna Kasarala

---

## 1. Project Overview

This project implements a **reliable, scalable, and maintainable batch-processing data architecture** for a data-intensive machine learning application. The system ingests, cleans, validates, and aggregates **NYC Taxi & Limousine Commission (TLC)** trip data — comprising millions of records per month — through a **Bronze → Silver → Gold medallion architecture**, all fully containerized using Docker Compose.

The entire infrastructure follows **Infrastructure as Code (IaC)** principles: a single `docker compose up -d` command launches **14 isolated microservices** on any machine with Docker installed, making the pipeline fully reproducible and portable across macOS, Linux, and Windows.

**Key capabilities:**

- Batch and streaming ingestion (direct download and Kafka-based)
- Distributed storage on HDFS with partition-based organization
- PySpark ETL with automated data quality checks
- Workflow orchestration via Apache Airflow
- Analytical data warehouse on PostgreSQL
- Business intelligence dashboards via Apache Superset

---

## 2. Architecture

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DATA ENGINEERING ARCHITECTURE                            │
│                     NYC Taxi TLC — Batch Processing Pipeline                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌──────────────┐                                                              │
│   │  NYC TLC S3  │  (External Data Source)                                      │
│   │  Parquet     │  https://d37ci6vzurychx.cloudfront.net/trip-data             │
│   └──────┬───────┘                                                              │
│          │                                                                      │
│          ▼                                                                      │
│   ┌─────────────────────────────────────────────────────┐                       │
│   │              INGESTION LAYER                        │                       │
│   │                                                     │                       │
│   │   Path A (Batch):        Path B (Streaming):        │                       │
│   │   download_nyc_tlc.py    kafka_producer.py           │                       │
│   │         │                      │                    │                       │
│   │         │                ┌─────▼──────┐             │                       │
│   │         │                │   KAFKA    │             │                       │
│   │         │                │  :9092     │             │                       │
│   │         │                │ (topic:    │             │                       │
│   │         │                │ trips_raw) │             │                       │
│   │         │                └─────┬──────┘             │                       │
│   │         │                      │                    │                       │
│   └─────────┼──────────────────────┼────────────────────┘                       │
│             │                      │                                            │
│             ▼                      ▼                                            │
│   ┌─────────────────────────────────────────────────────┐                       │
│   │          STORAGE & PROCESSING LAYER                 │                       │
│   │                                                     │                       │
│   │   ┌─────────────────┐    ┌─────────────────────┐    │                       │
│   │   │  HDFS CLUSTER   │    │   SPARK CLUSTER     │    │                       │
│   │   │                 │    │                     │    │                       │
│   │   │  NameNode :9870 │◄──►│  Master  :8080      │    │                       │
│   │   │  DataNode :9864 │    │  Worker  :8081      │    │                       │
│   │   │                 │    │  History :18081     │    │                       │
│   │   │  /datalake/nyc/ │    │                     │    │                       │
│   │   │  ├── bronze/    │    │  Spark Jobs:        │    │                       │
│   │   │  ├── silver/    │    │  ├ bronze_to_silver │    │                       │
│   │   │  └── gold/      │    │  ├ silver_to_gold   │    │                       │
│   │   │                 │    │  ├ dq_check_silver  │    │                       │
│   │   └─────────────────┘    │  └ evaluate_metrics │    │                       │
│   │                          └─────────┬───────────┘    │                       │
│   └────────────────────────────────────┼────────────────┘                       │
│                                        │                                        │
│                                        ▼                                        │
│   ┌─────────────────────────────────────────────────────┐                       │
│   │              SERVING LAYER                          │                       │
│   │                                                     │                       │
│   │   ┌──────────────┐   ┌────────────┐   ┌──────────┐ │                       │
│   │   │ POSTGRESQL   │   │  SUPERSET  │   │ ADMINER  │ │                       │
│   │   │    :5432     │──►│   :8089    │   │  :8082   │ │                       │
│   │   │              │   │ Dashboards │   │  DB UI   │ │                       │
│   │   │ Tables:      │   └────────────┘   └──────────┘ │                       │
│   │   │ fact_trips   │                                  │                       │
│   │   │ dq_results   │                                  │                       │
│   │   │ metrics_runs │                                  │                       │
│   │   │ taxi_zones   │                                  │                       │
│   │   └──────────────┘                                  │                       │
│   └─────────────────────────────────────────────────────┘                       │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────┐                       │
│   │           ORCHESTRATION LAYER                       │                       │
│   │                                                     │                       │
│   │   ┌──────────────────────────────────────────────┐  │                       │
│   │   │           APACHE AIRFLOW :8083               │  │                       │
│   │   │  ┌────────────┐  ┌───────────────────────┐   │  │                       │
│   │   │  │ Scheduler  │  │ DAGs:                 │   │  │                       │
│   │   │  │            │  │ ├ nyc_taxi_batch      │   │  │                       │
│   │   │  │ LocalExec  │  │ ├ nyc_taxi_kafka      │   │  │                       │
│   │   │  │            │  │ ├ load_taxi_zone      │   │  │                       │
│   │   │  └────────────┘  │ └ nyc_phase3_eval     │   │  │                       │
│   │   │                  └───────────────────────┘   │  │                       │
│   │   └──────────────────────────────────────────────┘  │                       │
│   └─────────────────────────────────────────────────────┘                       │
│                                                                                 │
│   Infrastructure: Docker Compose │ Network: de-net (bridge)                     │
│   All services: restart: unless-stopped │ Health checks on every service        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Pipeline Flow (Medallion Architecture)

```
┌────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│            │     │                │     │                │     │                │
│  RAW DATA  │────►│  BRONZE LAYER  │────►│  SILVER LAYER  │────►│   GOLD LAYER   │
│            │     │                │     │                │     │                │
│ NYC TLC S3 │     │ Raw Parquet    │     │ Cleaned Data   │     │ Monthly KPIs   │
│ Parquet    │     │ Partitioned    │     │ Validated      │     │ Aggregated     │
│            │     │ by year/month  │     │ Filtered       │     │ fact_trips_    │
│            │     │                │     │ trip_dist > 0  │     │ monthly        │
│            │     │ HDFS:          │     │ fare >= 0      │     │                │
│            │     │ /datalake/nyc/ │     │ HDFS:          │     │ HDFS + Postgres│
│            │     │ bronze/        │     │ /datalake/nyc/ │     │ /datalake/nyc/ │
│            │     │                │     │ silver/        │     │ gold/          │
└────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
                                                │
                                                ▼
                                   ┌────────────────────────┐
                                   │   DATA QUALITY CHECK   │
                                   │                        │
                                   │ Null rate  ≤ 5%        │
                                   │ Bad values ≤ 2%        │
                                   │ Results → dq_results   │
                                   └────────────────────────┘
```

---

## 3. Technology Stack

| Component             | Technology                        | Version  | Purpose                                |
|-----------------------|-----------------------------------|----------|----------------------------------------|
| Distributed Storage   | Apache Hadoop HDFS                | 3.2.1    | Scalable file system for raw & processed data |
| Batch Processing      | Apache Spark (PySpark)            | 3.1.2    | Distributed ETL transformations         |
| Message Queue         | Apache Kafka + Zookeeper          | 7.5.0    | Streaming ingestion backbone            |
| Workflow Orchestration| Apache Airflow                    | 2.9.3    | DAG-based pipeline scheduling           |
| Data Warehouse        | PostgreSQL                        | 15       | Analytical storage for KPIs & metrics   |
| Data Visualization    | Apache Superset                   | 3.1.0    | Dashboards & BI reporting               |
| Database Admin        | Adminer                           | 4        | Web-based PostgreSQL browser            |
| Containerization      | Docker & Docker Compose           | —        | Infrastructure as Code                  |
| Programming Language  | Python                            | 3.11     | ETL jobs, DAGs, scripts                 |

---

## 4. Repository Structure

```
DLMDSEDE02_DataEngineering_Phase3Submission2/
│
├── docker-compose.yml              # 14 services — entire infrastructure
├── .env                            # Compose project name
├── requirements.txt                # Project-wide Python dependencies
├── .gitignore                      # Git exclusion rules
├── README.md                       # This file
│
├── airflow/
│   ├── dags/                       # Airflow DAG definitions
│   │   ├── nyc_taxi_batch_dag.py         # Batch: Download → Bronze → Silver → Gold
│   │   ├── nyc_taxi_kafka_dag.py         # Kafka: Download → Kafka → Bronze → Silver → Gold
│   │   ├── nyc_phase3_eval.py            # DQ check on Silver + Gold metrics evaluation
│   │   └── spark_load_taxi.py            # Daily taxi zone lookup loader
│   ├── spark_jobs/                 # PySpark ETL jobs (submitted by Airflow)
│   │   ├── nyc_bronze_to_silver.py       # Ingest raw → Bronze; clean Bronze → Silver
│   │   ├── nyc_silver_to_gold.py         # Aggregate Silver → Gold KPIs → Postgres
│   │   ├── spark_kafka_to_bronze_batch.py# Consume Kafka topic → Bronze (append)
│   │   ├── dq_check_silver.py            # Data quality validation (null/bad rates)
│   │   └── evaluate_gold_metrics.py      # Pipeline execution metrics
│   └── requirements.txt            # Airflow container dependencies
│
├── app/                            # Standalone Spark applications
│   ├── spark_job.py                # Batch cleaning of taxi zone data → Postgres
│   └── load_taxi_zone.py           # Taxi zone lookup → Postgres reference table
│
├── scripts/                        # Utility & automation scripts
│   ├── run_e2e.sh                  # End-to-end pipeline test (HDFS → Spark → Postgres)
│   ├── verify.sh                   # Infrastructure health check across all services
│   ├── clean_docker.sh             # Docker cleanup (containers, volumes, images)
│   ├── download_jdbc.sh            # Download PostgreSQL JDBC driver JAR
│   ├── download_nyc_tlc.py         # Download NYC TLC trip data from S3
│   └── kafka_producer.py           # Produce Parquet records to Kafka topic
│
├── sql/                            # PostgreSQL initialization scripts
│   ├── init_postgres.sql           # Create pipeline tables (batch_clean, fact_trips, dq_results, etc.)
│   └── init_phase3_metrics.sql     # Job tracking table + performance indexes
│
├── datasets/                       # Reference datasets
│   └── taxi_zone_lookup.csv        # 265 NYC taxi zones (Borough, Zone, service_zone)
│
├── jars/                           # JDBC driver JARs
│   └── postgresql-42.6.0.jar       # PostgreSQL JDBC driver for Spark
│
└── docs/                           # Documentation & architecture
    ├── architecture/               # Architecture diagrams (HTML, DrawIO)
    ├── assignments/                # IU assignment PDFs
    ├── guides/                     # Setup guides, testing, code review
    └── proposals/                  # Pipeline proposal documents
```

---

## 5. Getting Started

### 5.1 Prerequisites

- **Docker Desktop** installed and running (allocate at least 6 GB RAM)
- **Git** installed
- **Internet connection** (to pull Docker images on first run)
- Compatible with macOS (including Apple Silicon), Linux, and Windows

### 5.2 Clone and Launch

```bash
# 1. Clone the repository
git clone https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02.git
cd DLMDSEDE02_DataEngineering_Phase3Submission2

# 2. Start all 14 services
docker compose up -d

# 3. Wait for initialization (~60-90 seconds for health checks to pass)
docker compose ps
```

On first launch, Docker will pull all images (~5 GB total). The `hdfs-bootstrap` container automatically loads reference CSV data into HDFS, and `airflow-init` migrates the Airflow database and creates the admin user.

### 5.3 Run the End-to-End Pipeline

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run full pipeline: HDFS bootstrap → Spark job → Postgres verification
./scripts/run_e2e.sh
```

### 5.4 Verify the System

```bash
# Check HDFS data
docker compose exec namenode hdfs dfs -ls /data/raw

# Check PostgreSQL tables
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT COUNT(*) FROM batch_clean;"
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT * FROM taxi_zone_lookup LIMIT 5;"

# Run full infrastructure verification
./scripts/verify.sh
```

### 5.5 Tear Down

```bash
# Stop containers (preserves data volumes)
docker compose down

# Stop and remove all volumes (clean slate)
docker compose down -v

# Full cleanup (removes images too)
./scripts/clean_docker.sh --full
```

---

## 6. Airflow DAGs

Access Airflow at **http://localhost:8083** (credentials: `airflow` / `airflow`).

| DAG | Schedule | Trigger | Description |
|-----|----------|---------|-------------|
| `nyc_taxi_batch` | `@monthly` | Auto / Manual | Full batch pipeline: download NYC TLC data from S3 → write to HDFS Bronze → clean to Silver → aggregate to Gold → load to PostgreSQL |
| `nyc_taxi_kafka_batch` | None | Manual | Kafka-based pipeline: download data → produce to Kafka topic `trips_raw` → consume to HDFS Bronze → Silver → Gold |
| `load_taxi_zone_lookup_daily` | `0 2 * * *` | Daily 02:00 UTC | Load taxi zone reference CSV into PostgreSQL `taxi_zone_lookup` table |
| `nyc_phase3_eval` | None | Manual | Run data quality checks on Silver layer + evaluate Gold layer metrics |

### DAG Task Graphs

**`nyc_taxi_batch`:**
```
prepare_dirs → download_dataset → spark_bronze → spark_silver → spark_gold
```

**`nyc_taxi_kafka_batch`:**
```
prepare_dirs → download_and_produce (→ Kafka) → spark_kafka_to_bronze → spark_silver → spark_gold
```

**`nyc_phase3_eval`:**
```
start → dq_check_silver → evaluate_gold_metrics → end
```

---

## 7. Data Pipeline Details

### 7.1 Bronze Layer (Raw Ingestion)

Raw Parquet files are ingested into HDFS and partitioned by `year` and `month`.

- **Batch path:** Downloaded from NYC TLC S3, written directly to HDFS
- **Kafka path:** Records produced to Kafka topic `trips_raw`, then consumed in batch by Spark and written to HDFS (append mode)
- **Location:** `hdfs:///datalake/nyc/bronze/yellow_tripdata/year=YYYY/month=MM`

### 7.2 Silver Layer (Cleaned & Validated)

PySpark applies quality filters and derives temporal columns.

- **Filters applied:** `trip_distance > 0` and `fare_amount >= 0`
- **Derived columns:** `pickup_date`, `year`, `month` (from `tpep_pickup_datetime`)
- **Partitioning:** Repartitioned and written by `year/month`
- **Location:** `hdfs:///datalake/nyc/silver/yellow_tripdata/year=YYYY/month=MM`

### 7.3 Gold Layer (Aggregated KPIs)

Monthly aggregations are calculated and stored in both HDFS and PostgreSQL.

| Metric | Calculation |
|--------|-------------|
| `trips` | COUNT(*) per year/month |
| `total_fare` | SUM(fare_amount) |
| `total_tip` | SUM(tip_amount) |
| `avg_distance` | AVG(trip_distance) |

- **HDFS location:** `hdfs:///datalake/nyc/gold/kpis_trips_monthly`
- **PostgreSQL table:** `public.fact_trips_monthly`

### 7.4 Data Quality Checks

The `dq_check_silver` job validates the Silver layer against configurable thresholds:

| Check | Threshold | Description |
|-------|-----------|-------------|
| Null rate (trip_distance) | ≤ 5% | Percentage of null trip_distance values |
| Null rate (fare_amount) | ≤ 5% | Percentage of null fare_amount values |
| Bad rate (trip_distance) | ≤ 2% | Percentage of trip_distance ≤ 0 |
| Bad rate (fare_amount) | ≤ 2% | Percentage of fare_amount < 0 |

Results are stored in `public.dq_results` with a unique `run_id` for audit trail.

---

## 8. PostgreSQL Database Schema

All tables are auto-created on first launch via SQL init scripts.

| Table | Purpose | Written By |
|-------|---------|------------|
| `batch_clean` | Cleaned taxi zone reference data | `app/spark_job.py` |
| `taxi_zone_lookup` | Taxi zone master reference (265 zones) | `app/load_taxi_zone.py` |
| `fact_trips_monthly` | Gold-layer monthly trip KPIs (PK: year, month) | `nyc_silver_to_gold.py` |
| `dq_results` | Data quality check results per run | `dq_check_silver.py` |
| `metrics_pipeline_runs` | Pipeline execution metrics per run | `evaluate_gold_metrics.py` |
| `job_runs` | Job execution tracking (name, status, rows) | Internal tracking |

---

## 9. Service URLs

Once all containers are healthy, the following UIs are accessible:

| Service | URL | Credentials |
|---------|-----|-------------|
| HDFS NameNode UI | http://localhost:9870 | — |
| HDFS DataNode UI | http://localhost:9864 | — |
| Spark Master UI | http://localhost:8080 | — |
| Spark Worker UI | http://localhost:8081 | — |
| Spark History Server | http://localhost:18081 | — |
| Airflow Web UI | http://localhost:8083 | `airflow` / `airflow` |
| Apache Superset | http://localhost:8089 | (setup required) |
| Adminer (DB browser) | http://localhost:8082 | Server: `postgres`, User: `nyc`, Pass: `nyc`, DB: `nyc` |
| PostgreSQL | localhost:5432 | `nyc` / `nyc` |
| Kafka Broker | localhost:9092 | — |
| Zookeeper | localhost:2181 | — |

---

## 10. Reliability, Scalability & Maintainability

### Reliability

- **HDFS replication** ensures data redundancy across DataNodes
- **PostgreSQL ACID transactions** guarantee data integrity in the warehouse
- **Docker health checks** on every critical service (HDFS, Postgres, Kafka, Airflow, Superset) with automatic restart (`unless-stopped` policy)
- **End-to-end verification scripts** confirm data flows from ingestion to serving
- **Data quality gates** in the pipeline prevent bad data from reaching Gold layer

### Scalability

- **Horizontal Spark scaling** — add additional `spark-worker-N` services in `docker-compose.yml`
- **HDFS DataNode expansion** — add more DataNodes for increased storage capacity
- **Kafka partitioning** — topic partitions enable parallel consumption
- **Container-based architecture** — ready for migration to Kubernetes for production scaling

### Maintainability

- **Infrastructure as Code** — all 14 services defined declaratively in `docker-compose.yml`
- **Version control** — entire codebase tracked in Git with meaningful commit history
- **Modular Spark jobs** — each transformation stage is an independent, testable Python script
- **Web monitoring UIs** — HDFS, Spark, Airflow, and Adminer provide real-time operational visibility
- **Separated concerns** — Airflow metadata database is isolated from the pipeline database

### Data Security, Governance & Protection

- **Network isolation** — all services communicate over a private Docker bridge network (`de-net`)
- **Credential management** — database credentials configured via environment variables
- **Separate metadata store** — Airflow uses its own PostgreSQL instance, isolating pipeline data from orchestration metadata
- **Audit trail** — every DQ check and pipeline run is logged with timestamps and unique run IDs in PostgreSQL
- **Automated health monitoring** — container health checks detect and auto-restart failed services

---

## 11. Troubleshooting

| Issue | Solution |
|-------|----------|
| Containers not starting | Ensure Docker Desktop is running with ≥ 6 GB RAM allocated |
| Port conflicts | Check for existing services on ports 9870, 8080, 8083, 5432, 9092 |
| Spark job fails | Verify HDFS has data: `docker compose exec namenode hdfs dfs -ls /data/raw` |
| JDBC driver missing | Run `./scripts/download_jdbc.sh` or use `--packages org.postgresql:postgresql:42.6.0` |
| Airflow DAGs not visible | Wait for `airflow-init` to complete, then restart scheduler: `docker compose restart airflow-scheduler` |
| Kafka connection issues | Ensure Zookeeper is healthy first: `docker compose logs zookeeper` |

View logs for any service:
```bash
docker compose logs -f <service-name>
# Example: docker compose logs -f spark-master
```

---

## 12. Data Source

**NYC Taxi & Limousine Commission (TLC) Trip Record Data**

- **URL:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **Format:** Apache Parquet
- **Volume:** 3+ million records per month
- **Time range:** Configurable (default: January 2023)
- **Types:** Yellow taxi, Green taxi, For-Hire Vehicle (FHV)
- **Columns used:** `tpep_pickup_datetime`, `tpep_dropoff_datetime`, `passenger_count`, `trip_distance`, `fare_amount`, `tip_amount`, `PULocationID`, `DOLocationID`, `payment_type`

---

## 13. Author

**Vamshi Krishna Kasarala**
IU International University of Applied Sciences
MSc Data Science — DLMDSEDE02 (Data Engineering)

**GitHub:** https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02
