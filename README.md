# DLMDSEDE02 — NYC Taxi Data Pipeline

> **IU International University of Applied Sciences** — MSc Data Science
> **Author:** Vamshi Krishna Kasarala | kasaralavamsi@gmail.com
> **Matriculation:** 92202958 | **Course:** DLMDSEDE02 (Data Engineering)
> **Repository:** https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02

Production-grade batch-processing data architecture using the **Medallion Architecture** (Bronze → Silver → Gold) on NYC Taxi & Limousine Commission trip data, fully containerised with Docker Compose across **15 microservices**.

---

## 📂 Code Location

> All runnable code lives in **[`DLMDSEDE02/`](DLMDSEDE02/)**

| File / Folder | Description |
|---|---|
| [`docker-compose.yml`](DLMDSEDE02/docker-compose.yml) | Launches all 15 microservices |
| [`Dockerfile.airflow`](DLMDSEDE02/Dockerfile.airflow) | Custom Airflow image with Java + Spark |
| [`airflow/dags/`](DLMDSEDE02/airflow/dags/) | All 4 Airflow DAGs |
| [`airflow/spark_jobs/`](DLMDSEDE02/airflow/spark_jobs/) | All 6 PySpark transformation jobs |
| [`sql/`](DLMDSEDE02/sql/) | PostgreSQL schema initialisation scripts |
| [`architecture_diagram.svg`](DLMDSEDE02/architecture_diagram.svg) | Full system architecture diagram |

```bash
# Quick start — 3 commands
git clone https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02.git
cd DataEngineering-DLMDSEDE02/DLMDSEDE02
docker compose up -d
```

---

## Architecture

```
NYC TLC CDN (Parquet)
        │
        ├─── Batch path ──────────────────────────────────────────────────┐
        │    download_nyc_tlc.py                                          │
        │    WebHDFS → HDFS Raw (/datalake/nyc/raw/)                      │
        │                                                                 │
        └─── Kafka path → Zookeeper → Kafka (trips_raw) ─────────────────┤
                          kafka_producer.py                               │
                                                                          ▼
                              Spark ──► HDFS Bronze → Silver → Gold (HDFS + PostgreSQL)
                                                                          │
                              Superset BI ◄─ PostgreSQL ◄─────────────────┘
                                             (fact_trips_monthly,
                                              taxi_zone_lookup,
                                              dq_results,
                                              metrics_pipeline_runs)
```

**Medallion layers (HDFS `hdfs://namenode:9000/datalake/nyc/`):**

| Layer | HDFS Path | Contents |
|-------|-----------|----------|
| Raw | `/raw/` | Original TLC Parquet files (staging before Bronze) |
| Bronze | `/bronze/yellow_tripdata/` | Raw Parquet, partitioned by year/month |
| Silver | `/silver/yellow_tripdata/` | Filtered (`trip_distance > 0`, `fare_amount ≥ 0`), typed |
| Gold | `/gold/kpis_trips_monthly/` | Monthly KPIs → also written to PostgreSQL `fact_trips_monthly` |

---

## Technology Stack

| Component | Version | Port(s) |
|-----------|---------|---------|
| Apache Airflow | 2.9.3 | 8083 |
| Apache Spark | 3.1.2 | 8090 (master) / 8081 (worker) / 18081 (history) |
| Apache Hadoop HDFS | 3.2.1 | 9870 (NameNode UI) / 9000 (RPC) / 9864 (DataNode) |
| Apache Kafka (Confluent) | **6.1.0** | 9092 |
| Zookeeper (Confluent) | **6.1.0** | 2181 |
| PostgreSQL | 15 | 5432 |
| Apache Superset | 3.1.0 | 8089 |
| Adminer | 4 | 8082 |

> ⚠️ **Kafka must be 6.1.0** (= Apache Kafka 2.7.x). Confluent 7.x uses Kafka 3.x which is incompatible with Spark 3.1.2's bundled `kafka-clients 2.6.0`.

---

## Quick Start

**Prerequisites:** Docker Desktop (16 GB RAM, 50 GB disk), Git, internet access.

```bash
# 1. Clone
git clone https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02.git
cd DataEngineering-DLMDSEDE02/DLMDSEDE02

# 2. Start all 15 services (~2–3 min first run)
docker compose up -d

# 3. Check health — all services should show (healthy)
docker compose ps
```

---

## Service URLs

| Service | URL | Login |
|---------|-----|-------|
| Airflow | http://localhost:8083 | airflow / airflow |
| Spark Master | http://localhost:8090 | — |
| Spark History | http://localhost:18081 | — |
| HDFS NameNode | http://localhost:9870 | — |
| Adminer | http://localhost:8082 | Server: `postgres` · User/Pass/DB: `nyc` |
| Superset | http://localhost:8089 | first-run setup |

---

## Running the Pipeline

### Step 1 — Load reference data (run once)
Enable and trigger `load_taxi_zone_lookup_daily` in Airflow. Loads 265 NYC taxi zones into `public.taxi_zone_lookup`.

### Step 2 — Batch pipeline
1. Open Airflow at http://localhost:8083
2. Enable and trigger `nyc_taxi_batch`
3. Task order: `prepare_dirs → download_dataset → spark_bronze → spark_silver → spark_gold`

### Step 3 — Kafka pipeline (alternative)
Enable and trigger `nyc_taxi_kafka_batch`. Task order: `prepare_dirs → download_and_produce → kafka_ready → spark_kafka_bronze → spark_silver → spark_gold`

### Step 4 — Data quality evaluation
Enable and trigger `nyc_phase3_eval` — runs Silver-layer DQ checks and records pipeline metrics.

### Verify results
```bash
docker compose exec postgres psql -U nyc -d nyc -c "SELECT * FROM fact_trips_monthly;"
docker compose exec namenode hdfs dfs -ls /datalake/nyc/
```

---

## DAGs

| DAG | Schedule | Purpose |
|-----|----------|---------|
| `nyc_taxi_batch` | @monthly | Full batch pipeline |
| `nyc_taxi_kafka_batch` | manual | Kafka ingestion variant |
| `nyc_phase3_eval` | manual | DQ checks + metrics evaluation |
| `load_taxi_zone_lookup_daily` | @daily 02:00 | Load 265 taxi zones into PostgreSQL |

---

## Project Structure

```
DLMDSEDE02/
├── Dockerfile.airflow             # Custom image: Ubuntu 22 + Java 17 + Spark 3.1.2 + Airflow 2.9.3
├── docker-compose.yml             # 15-service stack definition
├── architecture_diagram.svg       # Full system architecture diagram
├── architecture_diagram.png       # Architecture diagram (PNG)
├── airflow/
│   ├── dags/
│   │   ├── nyc_taxi_batch_dag.py          # Batch pipeline DAG
│   │   ├── nyc_taxi_kafka_dag.py          # Kafka streaming pipeline DAG
│   │   ├── nyc_phase3_eval.py             # DQ evaluation DAG
│   │   └── spark_load_taxi.py             # Taxi zone loader DAG
│   ├── spark_jobs/
│   │   ├── nyc_bronze_to_silver.py        # Bronze + Silver transforms
│   │   ├── nyc_silver_to_gold.py          # Gold KPI aggregation → HDFS + PostgreSQL
│   │   ├── spark_kafka_to_bronze_batch.py # Kafka consumer → HDFS Bronze
│   │   ├── dq_check_silver.py             # Data quality checks
│   │   ├── evaluate_gold_metrics.py       # Pipeline metrics evaluation
│   │   └── load_taxi_zone.py              # Taxi zone psycopg2 loader
│   └── requirements.txt
├── src/scripts/
│   ├── download_nyc_tlc.py                # TLC Parquet downloader
│   └── kafka_producer.py                  # Kafka record producer
├── sql/
│   ├── init_postgres.sql                  # Core table definitions
│   └── init_phase3_metrics.sql            # DQ + metrics tables
└── data/
    └── raw/                               # Downloaded TLC Parquet files
```

---

## PostgreSQL Schema

```sql
public.taxi_zone_lookup      (location_id, borough, zone, service_zone)
public.fact_trips_monthly    (year, month, total_trips, total_fare, total_tip, avg_distance)
public.dq_results            (run_id, layer, rule, total_rows, valid_rows, dq_score, run_at)
public.metrics_pipeline_runs (run_id, dag_id, total_rows_processed, exec_time_secs, run_at)
```

---

## Troubleshooting

**Containers unhealthy** — `docker compose down -v && docker compose up -d`

**Kafka version error** — image must be `confluentinc/cp-kafka:6.1.0`, not `7.x`

**HDFS NameNode in safe mode** — `docker compose exec namenode hdfs dfsadmin -safemode leave`

**spark_bronze FileNotFoundException** — executor cannot access local files; ensure `download_dataset` pushed an `hdfs://` URI to XCom

**Silver/Gold "Unable to infer schema"** — Bronze job produced no data; re-trigger `nyc_taxi_batch` from `spark_bronze`

**data/raw/ owned by root** — pre-create `mkdir -p DLMDSEDE02/data/raw` before `docker compose up -d`

---

- **GitHub:** https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02
- **Author:** Vamshi Krishna Kasarala (92202958) — DLMDSEDE02 Data Engineering, IU International University of Applied Sciences
