# DLMDSEDE02 DataEngineering Phase3 Submission

## 📌 Project Overview
This project is the **Phase 3 submission** for the IU course **DLMDSEDE02 – Data Engineering**.  
The goal is to design and implement a **batch-processing data architecture** for machine learning applications, integrating **HDFS, Spark, PostgreSQL, Airflow, Kafka, and Superset**.

---

## ⚙️ Tech Stack
- **Hadoop (HDFS)** – Distributed storage
- **Apache Spark** – Batch data processing
- **PostgreSQL** – Data warehouse / storage
- **Apache Airflow** – Workflow orchestration
- **Apache Kafka** – Streaming and messaging backbone
- **Apache Superset** – Data visualization & dashboards
- **Docker & Docker Compose** – Containerization & deployment

---

## 📂 Repository Structure
```
DLMDSEDE02_DataEngineering_Phase3Submission/
├── airflow/              # Airflow DAGs and configs
├── app/                  # Spark application code
├── datasets/             # Input datasets (e.g., taxi_zone_lookup.csv)
├── scripts/              # Utility scripts
├── sql/                  # SQL initialization scripts for PostgreSQL
├── docker-compose.yml    # Multi-service orchestration file
└── README.md             # Project documentation
```

---

## 🚀 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02.git
cd DLMDSEDE02_DataEngineering_Phase3Submission
```

### 2. Start the environment
```bash
docker compose up -d
```

### 3. Load datasets into HDFS
```bash
docker compose exec namenode hdfs dfs -mkdir -p /datasets
docker compose exec namenode hdfs dfs -put -f /datasets/taxi_zone_lookup.csv /datasets/
```

### 4. Verify PostgreSQL ingestion
```bash
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT * FROM taxi_zone_lookup LIMIT 5;"
```

### 5. Run Spark job
```bash
docker compose exec spark-master bash -lc "/spark/bin/spark-submit --master 'local[*]' /opt/spark/app/spark_job.py"
```

---

## 📊 Visualization
Once data pipelines are executed, Superset can be accessed at:

👉 [http://localhost:8089](http://localhost:8089)

---

## 👤 Author
**Vamshi Krishna Kasarla**  
IU MSc Data Science – DLMDSEDE02 (Data Engineering)  
