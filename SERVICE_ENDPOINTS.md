# Service Endpoints & Connection Details

Quick reference for accessing all services in the NYC Taxi Data Pipeline.

---

## 🗄️ PostgreSQL (Data Warehouse)

### Direct Connection
```
Host: localhost
Port: 5432
Username: nyc
Password: nyc
Database: nyc
```

### CLI Access
```bash
# Connect via psql
docker exec -it postgres psql -U nyc -d nyc

# Run a query
docker exec -it postgres psql -U nyc -d nyc -c "SELECT * FROM fact_trips_monthly LIMIT 5;"

# List all tables
docker exec -it postgres psql -U nyc -d nyc -c "\dt"
```

### JDBC URL (for applications)
```
jdbc:postgresql://localhost:5432/nyc
```

---

## 🌐 Adminer (PostgreSQL Web UI)

**URL:** http://localhost:8082

**Login:**
- System: `PostgreSQL`
- Server: `postgres`
- Username: `nyc`
- Password: `nyc`
- Database: `nyc`

---

## 📨 Apache Kafka (Streaming)

### Connection Details
```
Bootstrap Server: localhost:9092
Zookeeper: localhost:2181
```

### CLI Commands
```bash
# List topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Create a topic
docker exec kafka kafka-topics --create \
  --topic trips_raw \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1

# Produce messages
docker exec -it kafka kafka-console-producer \
  --topic trips_raw \
  --bootstrap-server localhost:9092

# Consume messages
docker exec -it kafka kafka-console-consumer \
  --topic trips_raw \
  --bootstrap-server localhost:9092 \
  --from-beginning
```

### Check Kafka Status
```bash
# Check broker API versions
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Check logs
docker logs kafka
docker logs zookeeper
```

---

## 🌊 Apache Airflow (Orchestration)

**URL:** http://localhost:8083

**Login:**
- Username: `airflow`
- Password: `airflow`

### CLI Commands
```bash
# List DAGs
docker exec airflow-webserver airflow dags list

# Trigger a DAG
docker exec airflow-webserver airflow dags trigger nyc_taxi_batch

# View task logs
docker exec airflow-webserver airflow tasks list nyc_taxi_batch

# Pause/Unpause DAG
docker exec airflow-webserver airflow dags pause nyc_taxi_batch
docker exec airflow-webserver airflow dags unpause nyc_taxi_batch
```

---

## ⚡ Apache Spark

### Spark Master UI
**URL:** http://localhost:8080

View running jobs, workers, and cluster resources.

### Spark Worker UI
**URL:** http://localhost:8081

Monitor individual worker status and tasks.

### Spark History Server
**URL:** http://localhost:18081

View completed Spark job history.

### Submit Jobs
```bash
# Submit a Spark job
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages org.postgresql:postgresql:42.6.0 \
  /opt/spark/app/spark_job.py

# Submit PySpark job from Airflow
docker exec airflow-scheduler spark-submit \
  --master spark://spark-master:7077 \
  /opt/airflow/spark_jobs/nyc_bronze_to_silver.py
```

---

## 🗂️ HDFS (Hadoop Distributed File System)

### NameNode UI
**URL:** http://localhost:9870

Browse HDFS file system and view cluster health.

### CLI Commands
```bash
# List files in HDFS
docker exec namenode hdfs dfs -ls /data/raw

# Upload file to HDFS
docker exec namenode hdfs dfs -put /local/path/file.csv /data/raw/

# Download file from HDFS
docker exec namenode hdfs dfs -get /data/raw/file.csv /local/path/

# Check HDFS disk usage
docker exec namenode hdfs dfs -df -h

# View file contents
docker exec namenode hdfs dfs -cat /data/raw/file.csv | head -20
```

---

## 📊 Apache Superset (Business Intelligence)

**URL:** http://localhost:8089

**Setup Required:**
```bash
# First-time setup
docker exec -it superset superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@example.com \
  --password admin

docker exec -it superset superset db upgrade
docker exec -it superset superset init
```

**Login:**
- Username: `admin`
- Password: `admin`

---

## 🔍 Quick Status Check

### Check All Services
```bash
# View all containers
docker compose ps

# Run diagnostic script
./scripts/diagnose_services.sh

# Check specific service logs
docker logs postgres
docker logs kafka
docker logs airflow-webserver
docker logs spark-master
```

### Health Check URLs
```bash
# Airflow
curl http://localhost:8083/health

# Superset
curl http://localhost:8088/health

# HDFS NameNode
curl http://localhost:9870/jmx
```

---

## 📋 All Service Ports

| Service | Port(s) | Purpose |
|---------|---------|---------|
| PostgreSQL | 5432 | Database connections |
| Adminer | 8082 | Database web UI |
| Kafka | 9092 | Kafka broker |
| Zookeeper | 2181 | Kafka coordination |
| HDFS NameNode | 9000, 9870 | HDFS RPC, Web UI |
| HDFS DataNode | 9864 | DataNode Web UI |
| Spark Master | 7077, 8080 | Cluster port, Web UI |
| Spark Worker | 8081 | Worker Web UI |
| Spark History | 18081 | History Server UI |
| Airflow Webserver | 8083 | Airflow Web UI |
| Superset | 8089 | Superset Web UI |

---

## 🚨 Common Issues

### PostgreSQL not accessible
```bash
# Check if container is healthy
docker compose ps postgres

# Wait for initialization (can take 30-60 seconds)
docker logs postgres | grep "ready to accept connections"

# Restart PostgreSQL
docker compose restart postgres
```

### Kafka not accessible
```bash
# Check if Zookeeper is running first
docker compose ps zookeeper

# Check Kafka logs
docker logs kafka

# Restart Kafka and Zookeeper
docker compose restart zookeeper kafka
```

### Port already in use
```bash
# Find what's using the port (example: 5432)
lsof -i :5432

# Kill the process
kill -9 <PID>

# Or change the port in docker-compose.yml
```

---

## 🔄 Restart Services

```bash
# Restart specific service
docker compose restart postgres
docker compose restart kafka

# Restart all services
docker compose restart

# Stop and start (clears state)
docker compose down
docker compose up -d
```

---

## 🧹 Clean Reset

If nothing works, perform a clean reset:

```bash
# Stop and remove everything (⚠️ DELETES ALL DATA)
docker compose down -v

# Start fresh
docker compose up -d

# Wait for services to be healthy
watch -n 2 'docker compose ps'
```

---

**For detailed troubleshooting, see:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
