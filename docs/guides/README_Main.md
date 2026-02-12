# DLMDSEDE02 DataEngineering Phase3 Submission

## Project Overview
This project is the **Phase 3 submission** for the IU course **DLMDSEDE02 – Data Engineering**.
The goal is to design and implement a **batch-processing data architecture** for machine learning applications, integrating **HDFS, Spark, PostgreSQL, Airflow, Kafka, and Superset**.

---

## Tech Stack
- **Hadoop (HDFS)** – Distributed storage (NameNode + DataNode)
- **Apache Spark 3.1.2** – Batch data processing (Master + Worker + History Server)
- **PostgreSQL 15** – Data warehouse / storage
- **Apache Airflow 2.9.3** – Workflow orchestration (Webserver + Scheduler)
- **Apache Kafka 3.4** – Streaming and messaging backbone (+ Zookeeper)
- **Apache Superset 3.1.0** – Data visualization & dashboards
- **Docker & Docker Compose** – Containerization & deployment

---

## Repository Structure
```
DLMDSEDE02_DataEngineering_Phase3Submission/
├── airflow/
│   ├── dags/                     # Airflow DAG definitions
│   │   ├── nyc_taxi_batch_dag.py       # Batch pipeline DAG
│   │   ├── nyc_taxi_kafka_dag.py       # Kafka-based pipeline DAG
│   │   ├── nyc_phase3_eval.py          # DQ + evaluation DAG
│   │   └── spark_load_taxi.py          # Zone lookup daily load DAG
│   ├── spark_jobs/               # Spark ETL jobs
│   │   ├── spark_kafka_to_bronze_batch.py
│   │   ├── nyc_bronze_to_silver.py
│   │   ├── nyc_silver_to_gold.py
│   │   ├── dq_check_silver.py
│   │   └── evaluate_gold_metrics.py
│   └── requirements.txt          # Airflow Python dependencies
├── app/                          # Standalone Spark applications
│   ├── spark_job.py              # Phase 3 batch cleaning job
│   └── load_taxi_zone.py         # Taxi zone lookup loader
├── datasets/                     # Input datasets
│   └── taxi_zone_lookup.csv
├── jars/                         # JDBC driver JARs
│   └── postgresql-42.6.0.jar
├── scripts/                      # Utility scripts
│   ├── kafka_producer.py         # Parquet-to-Kafka producer
│   ├── download_nyc_tlc.py       # NYC TLC dataset downloader
│   ├── download_jdbc.sh          # JDBC JAR downloader
│   ├── run_e2e.sh                # End-to-end test runner
│   └── verify.sh                 # Infrastructure verifier
├── sql/                          # PostgreSQL init scripts
│   ├── init_postgres.sql         # All pipeline tables
│   └── init_phase3_metrics.sql   # Job tracking + indexes
├── docker-compose.yml            # Multi-service orchestration
├── requirements.txt              # Project-wide Python dependencies
├── .gitignore
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02.git
cd DLMDSEDE02_DataEngineering_Phase3Submission
```

### 2. Start the environment
```bash
docker compose up -d
```
This starts all services: HDFS, Spark, PostgreSQL, Kafka, Airflow (with its own metadata DB), and Superset.
The `hdfs-bootstrap` container automatically loads CSV datasets into HDFS.
Airflow dependencies are auto-installed from `airflow/requirements.txt` during initialization.

### 3. Verify HDFS data
```bash
docker compose exec namenode hdfs dfs -ls /data/raw
```

### 4. Run standalone Spark job (with JDBC driver)
```bash
docker compose exec spark-master bash -lc "/spark/bin/spark-submit \
  --packages org.postgresql:postgresql:42.6.0 \
  --master 'local[*]' \
  /opt/spark/app/spark_job.py"
```

### 5. Verify PostgreSQL ingestion
```bash
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT COUNT(*) FROM batch_clean;"
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT * FROM taxi_zone_lookup LIMIT 5;"
```

---

## Service URLs

| Service          | URL                          | Credentials          |
|------------------|------------------------------|----------------------|
| HDFS NameNode    | http://localhost:9870        | –                    |
| Spark Master     | http://localhost:8080        | –                    |
| Spark Worker     | http://localhost:8081        | –                    |
| Spark History    | http://localhost:18081       | –                    |
| Airflow UI       | http://localhost:8083        | airflow / airflow    |
| Superset         | http://localhost:8089        | (setup required)     |
| Adminer (DB UI)  | http://localhost:8082        | nyc / nyc            |
| PostgreSQL       | localhost:5432               | nyc / nyc            |
| Kafka            | localhost:9092               | –                    |

---

## Airflow DAGs

| DAG Name                     | Schedule  | Description                                      |
|------------------------------|-----------|--------------------------------------------------|
| `nyc_taxi_batch`             | @monthly  | Download → Bronze → Silver → Gold (batch)        |
| `nyc_taxi_kafka_batch`       | Manual    | Download → Kafka → Bronze → Silver → Gold        |
| `load_taxi_zone_lookup_daily`| Daily 02:00 | Load taxi_zone_lookup.csv into PostgreSQL      |
| `nyc_phase3_eval`            | Manual    | DQ check on Silver + evaluate Gold metrics       |

---

## Architecture
Open `architecture_diagram.html` in a browser to see the full interactive architecture diagram.

---

## Author
**Vamshi Krishna Kasarla**
IU MSc Data Science – DLMDSEDE02 (Data Engineering)
