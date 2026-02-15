# DLMDSEDE02 — Data Engineering: Batch-Processing Data Architecture
## NYC Taxi Trip Data Pipeline with Medallion Architecture

> **IU International University of Applied Sciences**
> MSc Data Science — DLMDSEDE02 (Data Engineering)
> **Author:** Vamshi Krishna Kasarala
> **Repository:** https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [End-to-End Data Flow](#3-end-to-end-data-flow)
4. [Technology Stack](#4-technology-stack)
5. [Getting Started](#5-getting-started)
6. [Complete Setup Guide](#6-complete-setup-guide)
7. [Pipeline Execution](#7-pipeline-execution)
8. [Data Quality & Validation](#8-data-quality--validation)
9. [Monitoring & Observability](#9-monitoring--observability)
10. [Troubleshooting](#10-troubleshooting)
11. [Performance & Scalability](#11-performance--scalability)
12. [Project Structure](#12-project-structure)

---

## 1. Project Overview

### 1.1 Problem Statement

Modern data-intensive applications require robust data architectures capable of:
- **Ingesting** millions of records from external sources
- **Processing** data with quality validations and transformations
- **Serving** analytical insights to business intelligence tools
- **Scaling** horizontally as data volumes grow
- **Maintaining** data lineage and audit trails

### 1.2 Solution

This project implements a **production-grade batch-processing data architecture** using the **Medallion Architecture** pattern (Bronze → Silver → Gold) to process NYC Taxi & Limousine Commission trip data.

**Key Features:**
- ✅ **14 Containerized Microservices** - Full stack deployed via Docker Compose
- ✅ **Infrastructure as Code** - Single command deployment (`docker compose up -d`)
- ✅ **Dual Ingestion Paths** - Batch download + Kafka streaming
- ✅ **Data Quality Gates** - Automated validation at each layer
- ✅ **Workflow Orchestration** - Apache Airflow DAGs
- ✅ **Distributed Processing** - Apache Spark with PySpark
- ✅ **Distributed Storage** - Apache Hadoop HDFS
- ✅ **Analytical Warehouse** - PostgreSQL with fact/dimension tables
- ✅ **Business Intelligence** - Apache Superset dashboards
- ✅ **Full Reproducibility** - Cross-platform (Mac, Linux, Windows)

### 1.3 Data Source

**NYC Taxi & Limousine Commission (TLC) Trip Records**
- **Source:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **Format:** Apache Parquet (columnar storage)
- **Volume:** 3+ million records per month
- **Time Range:** Configurable (default: January 2023)
- **Update Frequency:** Monthly

**Schema (Yellow Taxi):**
```
├── tpep_pickup_datetime    (timestamp)
├── tpep_dropoff_datetime   (timestamp)
├── passenger_count         (integer)
├── trip_distance           (double)
├── fare_amount             (double)
├── tip_amount              (double)
├── total_amount            (double)
├── PULocationID            (integer)
├── DOLocationID            (integer)
└── payment_type            (integer)
```

---

## 2. Architecture

### 2.1 High-Level System Architecture

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

### 2.2 Medallion Architecture Layers

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

**Bronze Layer** - Raw Data Lake
- **Purpose:** Land raw data "as-is" from source
- **Format:** Parquet (compressed columnar)
- **Partitioning:** `year=YYYY/month=MM`
- **Location:** `hdfs:///datalake/nyc/bronze/yellow_tripdata/`
- **Retention:** Indefinite (source of truth)
- **Schema Evolution:** Supported via Parquet

**Silver Layer** - Cleaned & Validated
- **Purpose:** Business-ready cleaned data
- **Transformations:**
  - Filter invalid records (`trip_distance > 0`, `fare_amount >= 0`)
  - Derive temporal columns (`pickup_date`, `year`, `month`)
  - Standardize data types
  - Remove duplicates
- **Location:** `hdfs:///datalake/nyc/silver/yellow_tripdata/`
- **Quality Gates:** Automated DQ checks
- **Usage:** Analytics, ML feature engineering

**Gold Layer** - Business Aggregates
- **Purpose:** Serve analytical KPIs
- **Aggregations:**
  - `trips` - COUNT(*) per month
  - `total_fare` - SUM(fare_amount)
  - `total_tip` - SUM(tip_amount)
  - `avg_distance` - AVG(trip_distance)
- **Storage:** HDFS + PostgreSQL (dual write)
- **Usage:** BI dashboards, reports

### 2.3 Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE STACK                      │
│                  (14 Microservices on de-net)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Storage Tier                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ NameNode     │  │ DataNode     │  │ PostgreSQL   │      │
│  │ :9870        │  │ :9864        │  │ :5432        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  Processing Tier                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Spark Master │  │ Spark Worker │  │ Spark History│      │
│  │ :8080        │  │ :8081        │  │ :18081       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  Messaging Tier                                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Kafka        │  │ Zookeeper    │                        │
│  │ :9092        │  │ :2181        │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                             │
│  Orchestration Tier                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Airflow Web  │  │ Airflow Sch  │  │ Airflow Init │      │
│  │ :8083        │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  Serving Tier                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Superset     │  │ Adminer      │  │ HDFS Bootstrap│     │
│  │ :8089        │  │ :8082        │  │ (init only)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  Network: de-net (bridge) │ All containers auto-restart     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. End-to-End Data Flow

### 3.1 Complete Pipeline Flow (Batch Path)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    BATCH PIPELINE END-TO-END FLOW                        │
└──────────────────────────────────────────────────────────────────────────┘

STEP 1: TRIGGER AIRFLOW DAG
┌─────────────────────────────────────────┐
│  User Action or Scheduler               │
│  ├─ Manual: Airflow UI trigger button   │
│  └─ Auto: @monthly cron schedule        │
└───────────────┬─────────────────────────┘
                ▼
        ┌───────────────┐
        │ nyc_taxi_batch│  DAG instantiated
        │     DAG       │
        └───────┬───────┘
                │
                ▼
STEP 2: PREPARE DIRECTORIES
┌─────────────────────────────────────────┐
│  Task: prepare_dirs (BashOperator)      │
│  Action: Create HDFS directories        │
│  ├─ hdfs dfs -mkdir -p /datalake/nyc/   │
│  ├─ hdfs dfs -mkdir -p /datalake/nyc/   │
│  │   bronze/yellow_tripdata/            │
│  ├─ hdfs dfs -mkdir -p /datalake/nyc/   │
│  │   silver/yellow_tripdata/            │
│  └─ hdfs dfs -mkdir -p /datalake/nyc/   │
│      gold/kpis_trips_monthly/           │
└───────────────┬─────────────────────────┘
                │
                ▼
STEP 3: DOWNLOAD DATA FROM NYC TLC S3
┌─────────────────────────────────────────┐
│  Task: download_dataset                 │
│  Script: scripts/download_nyc_tlc.py    │
│  ├─ Construct S3 URL for 2023-01       │
│  │   https://d37ci6vzurychx.cloud...   │
│  │   /trip-data/yellow_tripdata_       │
│  │   2023-01.parquet                   │
│  ├─ Download via HTTP GET (requests)   │
│  ├─ Save to /tmp/yellow_tripdata_      │
│  │   2023-01.parquet                   │
│  └─ Verify file size > 0                │
└───────────────┬─────────────────────────┘
                │ (3.2M records, ~50MB)
                ▼
STEP 4: INGEST TO BRONZE LAYER
┌─────────────────────────────────────────┐
│  Task: spark_bronze_job                 │
│  Job: nyc_bronze_to_silver.py           │
│  ├─ Read Parquet from /tmp              │
│  ├─ Add ingestion_timestamp column      │
│  ├─ Partition by year, month            │
│  │   (extract from tpep_pickup_datetime)│
│  ├─ Write to HDFS in Parquet format     │
│  │   Location: /datalake/nyc/bronze/    │
│  │   yellow_tripdata/year=2023/month=1/ │
│  └─ Mode: overwrite (idempotent)        │
└───────────────┬─────────────────────────┘
                │
                ▼
        [BRONZE LAYER COMPLETE]
        HDFS: 3.2M records partitioned
        Size: ~45MB compressed Parquet
                │
                ▼
STEP 5: CLEAN & TRANSFORM TO SILVER LAYER
┌─────────────────────────────────────────┐
│  Task: spark_silver_job                 │
│  Job: nyc_bronze_to_silver.py           │
│  ├─ Read from Bronze HDFS               │
│  ├─ Apply filters:                      │
│  │   ├─ trip_distance > 0               │
│  │   └─ fare_amount >= 0                │
│  ├─ Derive columns:                     │
│  │   ├─ pickup_date = DATE(timestamp)   │
│  │   ├─ year = YEAR(timestamp)          │
│  │   └─ month = MONTH(timestamp)        │
│  ├─ Drop nulls in critical columns      │
│  ├─ Repartition by year, month          │
│  ├─ Write to HDFS                       │
│  │   Location: /datalake/nyc/silver/    │
│  │   yellow_tripdata/year=2023/month=1/ │
│  └─ Mode: overwrite                     │
└───────────────┬─────────────────────────┘
                │
                ▼
        [SILVER LAYER COMPLETE]
        HDFS: 3.1M records (100K filtered out)
        Quality: 96.9% pass rate
                │
                ▼
STEP 6: DATA QUALITY VALIDATION (OPTIONAL)
┌─────────────────────────────────────────┐
│  Task: dq_check_silver (if triggered)   │
│  Job: dq_check_silver.py                │
│  ├─ Read Silver layer                   │
│  ├─ Calculate metrics:                  │
│  │   ├─ null_rate_trip_distance = 0.5%  │
│  │   ├─ null_rate_fare_amount = 0.3%    │
│  │   ├─ bad_rate_trip_distance = 0.0%   │
│  │   └─ bad_rate_fare_amount = 0.1%     │
│  ├─ Validate thresholds:                │
│  │   ├─ null_rate ≤ 5% ✓                │
│  │   └─ bad_rate ≤ 2% ✓                 │
│  ├─ Write results to PostgreSQL         │
│  │   Table: dq_results                  │
│  │   Columns: run_id, metric, value,    │
│  │            threshold, status, ts     │
│  └─ Status: PASS                        │
└───────────────┬─────────────────────────┘
                │
                ▼
STEP 7: AGGREGATE TO GOLD LAYER
┌─────────────────────────────────────────┐
│  Task: spark_gold_job                   │
│  Job: nyc_silver_to_gold.py             │
│  ├─ Read from Silver HDFS               │
│  ├─ Group by year, month                │
│  ├─ Aggregate:                          │
│  │   ├─ trips = COUNT(*)                │
│  │   ├─ total_fare = SUM(fare_amount)   │
│  │   ├─ total_tip = SUM(tip_amount)     │
│  │   └─ avg_distance = AVG(trip_dist)   │
│  ├─ Calculate derived metrics:          │
│  │   ├─ avg_fare_per_trip               │
│  │   └─ tip_percentage                  │
│  ├─ Dual Write:                         │
│  │   ├─ HDFS: /datalake/nyc/gold/       │
│  │   │   kpis_trips_monthly/            │
│  │   └─ PostgreSQL: fact_trips_monthly  │
│  │       (upsert via JDBC)              │
│  └─ Mode: append (no duplicates)        │
└───────────────┬─────────────────────────┘
                │
                ▼
        [GOLD LAYER COMPLETE]
        PostgreSQL: 1 row inserted
        Metrics available for BI
                │
                ▼
┌─────────────────────────────────────────┐
│  PIPELINE SUCCESS                       │
│  ├─ Duration: ~3 minutes                │
│  ├─ Records Processed: 3.2M             │
│  ├─ Records in Gold: 1 (monthly agg)    │
│  ├─ Data Quality: PASS                  │
│  └─ Status: Airflow DAG marked SUCCESS  │
└─────────────────────────────────────────┘
```

### 3.2 Kafka Streaming Path

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   KAFKA STREAMING PIPELINE FLOW                          │
└──────────────────────────────────────────────────────────────────────────┘

STEP 1: DOWNLOAD & PRODUCE TO KAFKA
┌─────────────────────────────────────────┐
│  Task: download_and_produce             │
│  Script: scripts/kafka_producer.py      │
│  ├─ Download Parquet from NYC TLC       │
│  ├─ Read with PyArrow                   │
│  ├─ Convert to JSON records             │
│  ├─ Produce to Kafka topic: trips_raw   │
│  │   ├─ Broker: kafka:9092              │
│  │   ├─ Partition key: pickup_date      │
│  │   └─ Compression: snappy             │
│  └─ Records produced: 3.2M               │
└───────────────┬─────────────────────────┘
                │
                ▼
        ┌──────────────┐
        │ Kafka Broker │  Topic: trips_raw
        │ (in-memory)  │  Partitions: 3
        └──────┬───────┘  Retention: 24h
               │
               ▼
STEP 2: CONSUME FROM KAFKA TO BRONZE
┌─────────────────────────────────────────┐
│  Task: spark_kafka_to_bronze            │
│  Job: spark_kafka_to_bronze_batch.py    │
│  ├─ Spark Structured Streaming          │
│  ├─ Read from Kafka topic                │
│  ├─ Trigger: availableNow (batch mode)  │
│  ├─ Parse JSON values                   │
│  ├─ Write to HDFS Bronze                │
│  │   Mode: append                       │
│  └─ Checkpoint: /tmp/kafka_checkpoint   │
└───────────────┬─────────────────────────┘
                │
                ▼
        [Then follows same Silver → Gold flow as batch]
```

### 3.3 Data Lineage & Audit Trail

```
Every record maintains:
┌───────────────────────────────────────┐
│ Lineage Metadata                      │
├───────────────────────────────────────┤
│ ingestion_timestamp   TIMESTAMP       │  ← Bronze layer
│ processing_timestamp  TIMESTAMP       │  ← Silver layer
│ source_file           VARCHAR         │  ← Original filename
│ pipeline_run_id       UUID            │  ← Airflow run_id
│ data_quality_status   VARCHAR         │  ← PASS/FAIL/SKIP
└───────────────────────────────────────┘

Stored in:
- HDFS: Parquet metadata
- PostgreSQL: job_runs table
- Airflow: XCom for inter-task communication
```

---

## 4. Technology Stack

### 4.1 Component Matrix

| Layer | Component | Version | Purpose | Port | Data Path |
|-------|-----------|---------|---------|------|-----------|
| **Storage** | Apache Hadoop HDFS | 3.2.1 | Distributed file system | 9870, 9864 | Raw → Processed data |
| **Storage** | PostgreSQL | 15 | Relational warehouse | 5432 | Gold layer KPIs |
| **Processing** | Apache Spark | 3.1.2 | Distributed ETL | 8080, 8081, 18081 | Bronze → Silver → Gold |
| **Messaging** | Apache Kafka | 7.5.0 | Message streaming | 9092 | Alternative ingestion |
| **Messaging** | Apache Zookeeper | 3.7 | Kafka coordination | 2181 | - |
| **Orchestration** | Apache Airflow | 2.9.3 | Workflow DAGs | 8083 | - |
| **Visualization** | Apache Superset | 3.1.0 | BI dashboards | 8089 | Gold layer queries |
| **Admin** | Adminer | 4 | Database UI | 8082 | PostgreSQL admin |
| **Container** | Docker | Latest | Containerization | - | - |
| **Language** | Python | 3.11 | ETL, DAGs, scripts | - | - |

### 4.2 Spark Job Dependencies

```python
# PySpark Jobs use:
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, to_date, count, sum, avg
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# PostgreSQL JDBC Driver:
postgresql-42.6.0.jar (mounted in /opt/spark/jars/)
```

### 4.3 Network Architecture

```
┌─────────────────────────────────────────┐
│   Docker Network: de-net (bridge)       │
├─────────────────────────────────────────┤
│ Subnet: 172.18.0.0/16                   │
│ Gateway: 172.18.0.1                     │
│                                         │
│ Service Discovery: DNS-based            │
│ ├─ namenode → 172.18.0.10               │
│ ├─ datanode → 172.18.0.11               │
│ ├─ spark-master → 172.18.0.20           │
│ ├─ postgres → 172.18.0.30               │
│ └─ kafka → 172.18.0.40                  │
│                                         │
│ External Access: Port forwarding        │
│ ├─ localhost:9870 → namenode:9870      │
│ ├─ localhost:8080 → spark-master:8080  │
│ └─ localhost:8083 → airflow-web:8083   │
└─────────────────────────────────────────┘
```

---

## 5. Getting Started

### 5.1 Prerequisites

**System Requirements:**
- **CPU:** 4+ cores recommended
- **RAM:** 8 GB minimum (6 GB allocated to Docker)
- **Disk:** 10 GB free space
- **OS:** macOS (Intel/Apple Silicon), Linux, Windows 10/11

**Required Software:**
```bash
# Docker Desktop (includes Docker Compose)
# Version: 20.10+ recommended
docker --version
docker compose version

# Git (for cloning repository)
git --version

# Internet connection (for image downloads ~5GB on first run)
```

### 5.2 Quick Start (3 Commands)

```bash
# 1. Clone repository
git clone https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02.git
cd DLMDSEDE02_DataEngineering_Phase3Submission2

# 2. Start all services
docker compose up -d

# 3. Wait for health checks (~60-90 seconds)
docker compose ps
```

**Expected Output:**
```
NAME                    IMAGE                       STATUS
airflow-init            apache/airflow:2.9.3        Exited (0)
airflow-scheduler       apache/airflow:2.9.3        Up (healthy)
airflow-webserver       apache/airflow:2.9.3        Up (healthy)
datanode                bde2020/hadoop-datanode     Up (healthy)
hdfs-bootstrap          bde2020/hadoop-namenode     Exited (0)
kafka                   confluentinc/cp-kafka       Up
namenode                bde2020/hadoop-namenode     Up (healthy)
postgres                postgres:15                 Up (healthy)
spark-history           bitnami/spark:3.1.2         Up
spark-master            bitnami/spark:3.1.2         Up
spark-worker            bitnami/spark:3.1.2         Up
superset                apache/superset:3.1.0       Up
zookeeper               confluentinc/cp-zookeeper   Up
```

### 5.3 Service URLs

Once all containers show `Up (healthy)`, access:

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Airflow** | http://localhost:8083 | airflow / airflow | Trigger DAGs, monitor jobs |
| **HDFS NameNode** | http://localhost:9870 | - | Browse HDFS files |
| **Spark Master** | http://localhost:8080 | - | Monitor Spark jobs |
| **Spark History** | http://localhost:18081 | - | View completed Spark jobs |
| **PostgreSQL** | localhost:5432 | nyc / nyc | Query warehouse |
| **Adminer** | http://localhost:8082 | Server: postgres<br>User: nyc<br>Password: nyc<br>Database: nyc | Database admin UI |
| **Superset** | http://localhost:8089 | (setup required) | BI dashboards |
| **Kafka** | localhost:9092 | - | Kafka broker |

---

## 6. Complete Setup Guide

### 6.1 Step-by-Step First Run

**Step 1: Verify Docker Resources**
```bash
# Check Docker has enough resources
docker info | grep -E "CPUs|Memory"

# Expected:
# CPUs: 4+
# Total Memory: 8+ GiB (with 6+ GiB available to Docker)
```

**Step 2: Clone & Navigate**
```bash
git clone https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02.git
cd DLMDSEDE02_DataEngineering_Phase3Submission2
ls -la  # Verify docker-compose.yml exists
```

**Step 3: Start Infrastructure**
```bash
# Pull all images (first time only, ~5GB download)
docker compose pull

# Start all services in detached mode
docker compose up -d

# Monitor startup logs
docker compose logs -f
# Press Ctrl+C when you see "Airflow is ready"
```

**Step 4: Verify Health**
```bash
# Check all services are healthy
docker compose ps

# Verify HDFS
docker compose exec namenode hdfs dfsadmin -report
# Expected: "Live datanodes (1):"

# Verify Spark
docker compose exec spark-master spark-submit --version
# Expected: "version 3.1.2"

# Verify PostgreSQL
docker compose exec postgres psql -U nyc -d nyc -c "SELECT version();"
# Expected: "PostgreSQL 15..."
```

**Step 5: Access Airflow UI**
```bash
# Open browser to http://localhost:8083
# Login: airflow / airflow

# You should see 4 DAGs:
# ├─ nyc_taxi_batch (paused)
# ├─ nyc_taxi_kafka_batch (paused)
# ├─ load_taxi_zone_lookup_daily (paused)
# └─ nyc_phase3_eval (paused)
```

### 6.2 Initialize Data

**Load Reference Data (Taxi Zones)**
```bash
# Execute taxi zone loader DAG via Airflow UI
# Or via CLI:
docker compose exec airflow-webserver airflow dags trigger load_taxi_zone_lookup_daily

# Verify loaded
docker compose exec postgres psql -U nyc -d nyc -c "SELECT COUNT(*) FROM taxi_zone_lookup;"
# Expected: 265
```

**Run End-to-End Test**
```bash
# Run automated E2E test
chmod +x scripts/run_e2e.sh
./scripts/run_e2e.sh

# Expected output:
# ✓ HDFS initialized
# ✓ Taxi zone data loaded
# ✓ Spark job completed
# ✓ PostgreSQL data verified
# SUCCESS: End-to-end pipeline validated
```

---

## 7. Pipeline Execution

### 7.1 Trigger Batch Pipeline (Manual)

**Via Airflow UI:**
1. Navigate to http://localhost:8083
2. Click on `nyc_taxi_batch` DAG
3. Click **Trigger DAG** button (play icon)
4. Monitor progress in Graph View

**Via Command Line:**
```bash
docker compose exec airflow-webserver airflow dags trigger nyc_taxi_batch

# Monitor execution
docker compose exec airflow-webserver airflow dags state nyc_taxi_batch

# View logs for specific task
docker compose exec airflow-webserver airflow tasks logs nyc_taxi_batch download_dataset <RUN_ID>
```

### 7.2 Pipeline Execution Timeline

```
Task Execution Flow (nyc_taxi_batch):
════════════════════════════════════════

START (T+0s)
  │
  ├─► prepare_dirs         [T+0s  → T+5s]   (5s)
  │
  ├─► download_dataset     [T+5s  → T+20s]  (15s)
  │
  ├─► spark_bronze_job     [T+20s → T+60s]  (40s)
  │
  ├─► spark_silver_job     [T+60s → T+120s] (60s)
  │
  └─► spark_gold_job       [T+120s → T+180s](60s)

END (T+180s = 3 minutes)
```

### 7.3 Monitoring Execution

**Airflow Task Status:**
```
Graph View:
┌─────────────────┐
│  prepare_dirs   │ ✓ success (green)
└────────┬────────┘
         │
┌────────▼────────┐
│download_dataset │ ✓ success (green)
└────────┬────────┘
         │
┌────────▼────────┐
│ spark_bronze_job│ ✓ success (green)
└────────┬────────┘
         │
┌────────▼────────┐
│ spark_silver_job│ ✓ success (green)
└────────┬────────┘
         │
┌────────▼────────┐
│  spark_gold_job │ ✓ success (green)
└─────────────────┘
```

**Spark Job Monitoring:**
```bash
# View Spark Master UI
open http://localhost:8080

# Check running applications
# ├─ Application ID: app-20231101120000-0001
# ├─ Name: Bronze to Silver Transformation
# ├─ Status: RUNNING
# └─ Duration: 45s

# View completed jobs in History Server
open http://localhost:18081
```

**HDFS Data Verification:**
```bash
# Check Bronze layer
docker compose exec namenode hdfs dfs -ls /datalake/nyc/bronze/yellow_tripdata/year=2023/month=1/

# Expected:
# Found 1 items
# -rw-r--r--   1 root supergroup  47238491 part-00000-*.parquet

# Check Silver layer
docker compose exec namenode hdfs dfs -ls /datalake/nyc/silver/yellow_tripdata/year=2023/month=1/

# Check Gold layer
docker compose exec namenode hdfs dfs -ls /datalake/nyc/gold/kpis_trips_monthly/
```

**PostgreSQL Data Verification:**
```bash
# Check Gold layer KPIs
docker compose exec postgres psql -U nyc -d nyc -c "
SELECT * FROM fact_trips_monthly
WHERE year = 2023 AND month = 1;
"

# Expected output:
#  year | month |  trips  | total_fare | total_tip | avg_distance
# ------+-------+---------+------------+-----------+--------------
#  2023 |     1 | 3109532 | 52847291.2 | 7234182.1 |         3.14
```

### 7.4 Kafka Pipeline Execution

```bash
# Trigger Kafka-based pipeline
docker compose exec airflow-webserver airflow dags trigger nyc_taxi_kafka_batch

# This will:
# 1. Download data
# 2. Produce to Kafka topic 'trips_raw'
# 3. Consume from Kafka to HDFS Bronze
# 4. Continue with Silver → Gold transformations

# Monitor Kafka topic
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic trips_raw \
  --max-messages 5

# Check consumer group lag
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group spark-kafka-consumer
```

---

## 8. Data Quality & Validation

### 8.1 Automated Data Quality Checks

**Silver Layer DQ Gates:**
```python
# Implemented in: airflow/spark_jobs/dq_check_silver.py

Quality Metrics Computed:
┌─────────────────────────────┬───────────┬───────────┐
│ Metric                      │ Threshold │ Action    │
├─────────────────────────────┼───────────┼───────────┤
│ null_rate_trip_distance     │ ≤ 5%      │ ALERT     │
│ null_rate_fare_amount       │ ≤ 5%      │ ALERT     │
│ bad_rate_trip_distance      │ ≤ 2%      │ FAIL      │
│ bad_rate_fare_amount        │ ≤ 2%      │ FAIL      │
│ duplicate_rate              │ ≤ 1%      │ WARN      │
└─────────────────────────────┴───────────┴───────────┘

Results stored in: public.dq_results
```

**Run Data Quality Check:**
```bash
# Trigger DQ DAG
docker compose exec airflow-webserver airflow dags trigger nyc_phase3_eval

# View results
docker compose exec postgres psql -U nyc -d nyc -c "
SELECT run_id, metric_name, metric_value, threshold_value, status, created_at
FROM dq_results
ORDER BY created_at DESC
LIMIT 10;
"
```

**Sample DQ Results:**
```
run_id    | metric_name              | metric_value | threshold | status | created_at
----------|--------------------------|--------------|-----------|--------|-------------------
uuid-123  | null_rate_trip_distance  | 0.5          | 5.0       | PASS   | 2023-11-01 12:00
uuid-123  | null_rate_fare_amount    | 0.3          | 5.0       | PASS   | 2023-11-01 12:00
uuid-123  | bad_rate_trip_distance   | 0.0          | 2.0       | PASS   | 2023-11-01 12:00
uuid-123  | bad_rate_fare_amount     | 0.1          | 2.0       | PASS   | 2023-11-01 12:00
```

### 8.2 Data Validation Rules

**Bronze Layer Validations:**
- ✓ File format: Parquet
- ✓ Schema matches expected structure
- ✓ Record count > 0
- ✓ Partitions created correctly

**Silver Layer Validations:**
- ✓ `trip_distance > 0`
- ✓ `fare_amount >= 0`
- ✓ `tpep_pickup_datetime IS NOT NULL`
- ✓ `passenger_count BETWEEN 1 AND 6`
- ✓ No duplicate records

**Gold Layer Validations:**
- ✓ Aggregation math correct (spot checks)
- ✓ No negative values
- ✓ Month/year combinations valid
- ✓ KPIs within expected ranges

---

## 9. Monitoring & Observability

### 9.1 Health Checks

**All containers have health checks:**
```yaml
# Example from docker-compose.yml
healthcheck:
  test: ["CMD", "pg_isready", "-U", "nyc"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

**Check Overall Health:**
```bash
# View health status
docker compose ps

# Check specific service logs
docker compose logs -f <service-name>

# Example:
docker compose logs -f spark-master
docker compose logs -f airflow-scheduler
docker compose logs -f postgres
```

### 9.2 System Verification Script

```bash
# Run comprehensive verification
chmod +x scripts/verify.sh
./scripts/verify.sh

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INFRASTRUCTURE VERIFICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# [1/7] Checking Docker containers...
#   ✓ namenode       (healthy)
#   ✓ datanode       (healthy)
#   ✓ spark-master   (healthy)
#   ✓ postgres       (healthy)
#   ✓ kafka          (healthy)
#   ✓ airflow-web    (healthy)
#
# [2/7] Verifying HDFS...
#   ✓ NameNode responsive
#   ✓ DataNode(s): 1 live
#   ✓ DFS Used: 2.5 GB
#
# [3/7] Verifying Spark...
#   ✓ Master URL: spark://spark-master:7077
#   ✓ Workers: 1 alive
#
# [4/7] Verifying PostgreSQL...
#   ✓ Connection successful
#   ✓ Database 'nyc' exists
#   ✓ Tables: 7 found
#
# [5/7] Verifying Kafka...
#   ✓ Broker: kafka:9092 reachable
#   ✓ Topics: trips_raw (3 partitions)
#
# [6/7] Verifying Airflow...
#   ✓ Web UI: http://localhost:8083 (200 OK)
#   ✓ DAGs loaded: 4
#
# [7/7] Verifying Network...
#   ✓ de-net bridge network active
#   ✓ All services can resolve each other
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ ALL CHECKS PASSED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 9.3 Metrics & Performance

**Pipeline Metrics Table (PostgreSQL):**
```sql
-- View pipeline execution metrics
SELECT
  run_id,
  pipeline_name,
  records_processed,
  execution_time_seconds,
  status,
  created_at
FROM metrics_pipeline_runs
ORDER BY created_at DESC
LIMIT 10;
```

**Spark Metrics:**
- **UI:** http://localhost:8080
- **Metrics:**
  - Tasks completed/failed
  - Shuffle read/write
  - Memory usage per executor
  - Job duration

**HDFS Metrics:**
- **UI:** http://localhost:9870
- **Metrics:**
  - DFS Used / Available
  - Block count
  - Replication factor status

---

## 10. Troubleshooting

### 10.1 Common Issues & Solutions

**Issue: Containers not starting**
```bash
# Check Docker resources
docker system df
docker system prune -a  # Clean up if needed

# Check resource allocation
docker info | grep -E "CPUs|Memory"
# Ensure: CPUs ≥ 4, Memory ≥ 8GB

# Restart Docker Desktop
# macOS: Docker Desktop → Preferences → Reset
# Linux: sudo systemctl restart docker
```

**Issue: Airflow UI not accessible**
```bash
# Check Airflow containers
docker compose ps | grep airflow

# View logs
docker compose logs airflow-webserver
docker compose logs airflow-scheduler

# Restart Airflow
docker compose restart airflow-webserver airflow-scheduler

# Re-init if needed
docker compose run --rm airflow-init
```

**Issue: HDFS NameNode in safe mode**
```bash
# Check safe mode status
docker compose exec namenode hdfs dfsadmin -safemode get

# Leave safe mode
docker compose exec namenode hdfs dfsadmin -safemode leave

# Verify
docker compose exec namenode hdfs dfs -ls /
```

**Issue: Spark job fails with OOM**
```bash
# Increase executor memory in docker-compose.yml
environment:
  - SPARK_EXECUTOR_MEMORY=2G  # Increase from 1G
  - SPARK_DRIVER_MEMORY=2G

# Restart Spark
docker compose restart spark-master spark-worker
```

**Issue: PostgreSQL connection refused**
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres | tail -50

# Test connection
docker compose exec postgres psql -U nyc -d nyc -c "SELECT 1;"

# Restart if needed
docker compose restart postgres
```

**Issue: Kafka consumer lag**
```bash
# Check consumer group
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group spark-kafka-consumer

# Reset offsets if needed
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group spark-kafka-consumer \
  --reset-offsets \
  --to-earliest \
  --execute \
  --topic trips_raw
```

### 10.2 Log Locations

```bash
# Airflow task logs
docker compose exec airflow-webserver ls -la /opt/airflow/logs/dag_id=nyc_taxi_batch/

# Spark application logs
docker compose logs spark-master | grep "Application"
docker compose logs spark-worker

# HDFS logs
docker compose exec namenode cat /hadoop/dfs/name/current/VERSION

# PostgreSQL logs
docker compose logs postgres
```

### 10.3 Reset & Clean Restart

```bash
# Stop all containers
docker compose down

# Remove all volumes (WARNING: deletes all data)
docker compose down -v

# Clean Docker system
docker system prune -a --volumes

# Fresh start
docker compose up -d

# Re-run initialization
./scripts/run_e2e.sh
```

---

## 11. Performance & Scalability

### 11.1 Current Performance Metrics

```
Baseline Performance (Single Spark Worker):
┌──────────────────────────────────────────┐
│ Dataset: 3.2M records (Jan 2023)         │
├──────────────────────────────────────────┤
│ Bronze Ingestion:    40 seconds          │
│ Silver Transform:    60 seconds          │
│ Gold Aggregation:    60 seconds          │
├──────────────────────────────────────────┤
│ Total Pipeline:      ~3 minutes          │
│ Throughput:          ~18,000 records/sec │
│ Storage (HDFS):      ~45 MB compressed   │
└──────────────────────────────────────────┘
```

### 11.2 Horizontal Scaling

**Add Spark Workers:**
```yaml
# In docker-compose.yml, duplicate spark-worker service:

spark-worker-2:
  image: bitnami/spark:3.1.2
  container_name: spark-worker-2
  environment:
    - SPARK_MODE=worker
    - SPARK_MASTER_URL=spark://spark-master:7077
    - SPARK_WORKER_MEMORY=2G
    - SPARK_WORKER_CORES=2
  networks:
    - de-net

# Restart:
docker compose up -d

# Verify:
# Open http://localhost:8080 → Workers: 2 alive
```

**Add HDFS DataNodes:**
```yaml
datanode-2:
  image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
  container_name: datanode-2
  environment:
    - CORE_CONF_fs_defaultFS=hdfs://namenode:9000
  volumes:
    - datanode2:/hadoop/dfs/data
  networks:
    - de-net

volumes:
  datanode2:
```

**Partitioning Strategy:**
```python
# Increase parallelism in Spark jobs
df.repartition(10)  # Distribute across more partitions

# Partition by multiple columns
df.write.partitionBy("year", "month", "day")
```

### 11.3 Optimization Best Practices

**1. Spark Optimizations:**
```python
# Enable adaptive query execution
spark.conf.set("spark.sql.adaptive.enabled", "true")

# Broadcast small DataFrames
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 10 * 1024 * 1024)  # 10MB

# Optimize shuffle partitions
spark.conf.set("spark.sql.shuffle.partitions", 200)
```

**2. HDFS Optimizations:**
```bash
# Increase replication for hot data
hdfs dfs -setrep -w 3 /datalake/nyc/silver/

# Use compression
df.write.option("compression", "snappy").parquet(path)
```

**3. PostgreSQL Optimizations:**
```sql
-- Create indexes on frequently queried columns
CREATE INDEX idx_fact_trips_year_month
ON fact_trips_monthly(year, month);

-- Analyze tables
ANALYZE fact_trips_monthly;

-- Vacuum regularly
VACUUM ANALYZE;
```

---

## 12. Project Structure

```
DLMDSEDE02_DataEngineering_Phase3Submission2/
│
├── 📁 airflow/                         # Airflow workflows
│   ├── dags/                           # DAG definitions
│   │   ├── nyc_taxi_batch_dag.py       # Main batch pipeline DAG
│   │   ├── nyc_taxi_kafka_dag.py       # Kafka streaming DAG
│   │   ├── nyc_phase3_eval.py          # DQ evaluation DAG
│   │   └── spark_load_taxi.py          # Taxi zone loader DAG
│   │
│   └── spark_jobs/                     # PySpark ETL jobs
│       ├── nyc_bronze_to_silver.py     # Bronze → Silver transform
│       ├── nyc_silver_to_gold.py       # Silver → Gold aggregation
│       ├── spark_kafka_to_bronze_batch.py  # Kafka → Bronze consumer
│       ├── dq_check_silver.py          # Data quality validation
│       └── evaluate_gold_metrics.py    # Pipeline metrics evaluation
│
├── 📁 app/                             # Standalone Spark applications
│   ├── spark_job.py                    # Taxi zone data cleaner
│   └── load_taxi_zone.py               # Load taxi zones to Postgres
│
├── 📁 scripts/                         # Utility scripts
│   ├── run_e2e.sh                      # End-to-end pipeline test
│   ├── verify.sh                       # Infrastructure health check
│   ├── clean_docker.sh                 # Docker cleanup utility
│   ├── download_jdbc.sh                # Download PostgreSQL JDBC driver
│   ├── download_nyc_tlc.py             # Download NYC TLC Parquet files
│   └── kafka_producer.py               # Produce Parquet to Kafka
│
├── 📁 sql/                             # PostgreSQL init scripts
│   ├── init_postgres.sql               # Create tables (batch_clean, fact_trips, etc.)
│   └── init_phase3_metrics.sql         # Job tracking table + indexes
│
├── 📁 datasets/                        # Reference datasets
│   └── taxi_zone_lookup.csv            # 265 NYC taxi zones (Borough, Zone)
│
├── 📁 jars/                            # JDBC drivers
│   └── postgresql-42.6.0.jar           # PostgreSQL JDBC driver for Spark
│
├── 📁 docs/                            # Documentation
│   ├── architecture/                   # Architecture diagrams (HTML, DrawIO)
│   ├── assignments/                    # IU assignment PDFs
│   ├── guides/                         # Setup guides, testing, code review
│   └── proposals/                      # Pipeline proposal documents
│
├── 📁 data/                            # Runtime data (not in repo)
├── 📁 config/                          # Configuration files
├── 📁 src/                             # Additional source code
│
├── 📄 docker-compose.yml               # 14-service infrastructure definition
├── 📄 requirements.txt                 # Python dependencies
├── 📄 .env                             # Environment variables
├── 📄 .gitignore                       # Git exclusion rules
├── 📄 README.md                        # This file
└── 📄 PROJECT_STRUCTURE.md             # Detailed project structure docs
```

---

## 13. Appendix

### 13.1 Service Dependencies Graph

```
┌─────────────┐
│  zookeeper  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    kafka    │
└─────────────┘

┌─────────────┐     ┌─────────────┐
│  namenode   │────►│  datanode   │
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│spark-master │────►│spark-worker │     │spark-history│
└──────┬──────┘     └─────────────┘     └─────────────┘
       │
       │            ┌─────────────┐
       └───────────►│  postgres   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  airflow-*  │
                    └─────────────┘

┌─────────────┐     ┌─────────────┐
│  superset   │────►│  postgres   │
└─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐
│   adminer   │────►│  postgres   │
└─────────────┘     └─────────────┘
```

### 13.2 Port Reference

| Port | Service | Protocol | Purpose |
|------|---------|----------|---------|
| 2181 | Zookeeper | TCP | Kafka coordination |
| 5432 | PostgreSQL | TCP | Database connections |
| 8080 | Spark Master | HTTP | Spark Master UI |
| 8081 | Spark Worker | HTTP | Spark Worker UI |
| 8082 | Adminer | HTTP | Database admin UI |
| 8083 | Airflow | HTTP | Airflow web UI |
| 8089 | Superset | HTTP | BI dashboards |
| 9000 | HDFS NameNode | TCP | HDFS RPC |
| 9092 | Kafka | TCP | Kafka broker |
| 9864 | HDFS DataNode | HTTP | DataNode UI |
| 9870 | HDFS NameNode | HTTP | NameNode UI |
| 18081 | Spark History | HTTP | Spark job history |

### 13.3 Environment Variables

```bash
# .env file
COMPOSE_PROJECT_NAME=dlmdsede02

# Hadoop
CORE_CONF_fs_defaultFS=hdfs://namenode:9000
HDFS_CONF_dfs_replication=1

# Spark
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_EXECUTOR_MEMORY=1G
SPARK_DRIVER_MEMORY=1G

# PostgreSQL
POSTGRES_USER=nyc
POSTGRES_PASSWORD=nyc
POSTGRES_DB=nyc

# Airflow
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://nyc:nyc@postgres/nyc
AIRFLOW__CORE__FERNET_KEY=<generated-key>
AIRFLOW__CORE__LOAD_EXAMPLES=False

# Kafka
KAFKA_BROKER_ID=1
KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
```

### 13.4 Useful Commands Cheat Sheet

```bash
# ═══════════════════════════════════════════════════════════
# DOCKER COMPOSE COMMANDS
# ═══════════════════════════════════════════════════════════

# Start all services
docker compose up -d

# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# View logs
docker compose logs -f <service-name>

# Restart specific service
docker compose restart <service-name>

# Check service status
docker compose ps

# Scale service
docker compose up -d --scale spark-worker=3

# ═══════════════════════════════════════════════════════════
# HDFS COMMANDS
# ═══════════════════════════════════════════════════════════

# List HDFS files
docker compose exec namenode hdfs dfs -ls /datalake/nyc/

# Create directory
docker compose exec namenode hdfs dfs -mkdir -p /path/to/dir

# Copy from local to HDFS
docker compose exec namenode hdfs dfs -put /local/file /hdfs/path

# Copy from HDFS to local
docker compose exec namenode hdfs dfs -get /hdfs/path /local/file

# Check HDFS health
docker compose exec namenode hdfs dfsadmin -report

# View file content
docker compose exec namenode hdfs dfs -cat /path/to/file

# ═══════════════════════════════════════════════════════════
# SPARK COMMANDS
# ═══════════════════════════════════════════════════════════

# Submit Spark job
docker compose exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  /path/to/job.py

# PySpark shell
docker compose exec spark-master pyspark

# Check Spark version
docker compose exec spark-master spark-submit --version

# ═══════════════════════════════════════════════════════════
# AIRFLOW COMMANDS
# ═══════════════════════════════════════════════════════════

# List DAGs
docker compose exec airflow-webserver airflow dags list

# Trigger DAG
docker compose exec airflow-webserver airflow dags trigger <dag-id>

# View DAG state
docker compose exec airflow-webserver airflow dags state <dag-id>

# View task logs
docker compose exec airflow-webserver airflow tasks logs <dag-id> <task-id> <run-id>

# Test task
docker compose exec airflow-webserver airflow tasks test <dag-id> <task-id> 2023-01-01

# ═══════════════════════════════════════════════════════════
# POSTGRESQL COMMANDS
# ═══════════════════════════════════════════════════════════

# Connect to PostgreSQL
docker compose exec postgres psql -U nyc -d nyc

# Run query
docker compose exec postgres psql -U nyc -d nyc -c "SELECT * FROM fact_trips_monthly;"

# List tables
docker compose exec postgres psql -U nyc -d nyc -c "\dt"

# Export table to CSV
docker compose exec postgres psql -U nyc -d nyc -c "\copy fact_trips_monthly TO '/tmp/export.csv' CSV HEADER"

# ═══════════════════════════════════════════════════════════
# KAFKA COMMANDS
# ═══════════════════════════════════════════════════════════

# List topics
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Describe topic
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic trips_raw

# Consume messages
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic trips_raw \
  --from-beginning \
  --max-messages 10

# Check consumer group lag
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group spark-kafka-consumer

# ═══════════════════════════════════════════════════════════
# VERIFICATION COMMANDS
# ═══════════════════════════════════════════════════════════

# Run end-to-end test
./scripts/run_e2e.sh

# Run infrastructure verification
./scripts/verify.sh

# Check all containers healthy
docker compose ps | grep "healthy"

# View resource usage
docker stats
```

---

## 14. Contributing & License

This project is developed as part of the IU International University Data Engineering course (DLMDSEDE02).

**Author:** Vamshi Krishna Kasarala
**Email:** kasaralavamsi@gmail.com
**GitHub:** https://github.com/kasaralavamsi
**LinkedIn:** [Your LinkedIn]

**For questions or support:**
- Open an issue on GitHub
- Email the author
- Consult the documentation in `/docs`

---

## 15. References

### 15.1 Official Documentation

- **NYC TLC Data:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **Apache Hadoop:** https://hadoop.apache.org/docs/r3.2.1/
- **Apache Spark:** https://spark.apache.org/docs/3.1.2/
- **Apache Kafka:** https://kafka.apache.org/documentation/
- **Apache Airflow:** https://airflow.apache.org/docs/apache-airflow/2.9.3/
- **PostgreSQL:** https://www.postgresql.org/docs/15/
- **Apache Superset:** https://superset.apache.org/docs/intro
- **Docker Compose:** https://docs.docker.com/compose/

### 15.2 Medallion Architecture Pattern

- **Databricks Medallion Architecture:** https://www.databricks.com/glossary/medallion-architecture
- **Data Lake Best Practices**
- **Delta Lake Documentation**

---

**🎉 Your NYC Taxi Data Pipeline is ready!**

Start exploring data with:
```bash
docker compose up -d
open http://localhost:8083  # Airflow UI
open http://localhost:8080  # Spark UI
open http://localhost:9870  # HDFS UI
```

Happy Data Engineering! 🚀
