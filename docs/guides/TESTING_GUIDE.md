# Phase 3 Pipeline Testing Guide

## Quick Test Checklist

Run these commands in order to verify everything works:

```bash
# 1. Check all services are running
docker compose ps

# 2. Run automated verification
./scripts/verify.sh

# 3. Test Airflow pipeline
# Open http://localhost:8083 (airflow/airflow)
# Trigger DAG: nyc_taxi_batch

# 4. Verify HDFS data
docker compose exec namenode hdfs dfs -ls /datalake/nyc/bronze

# 5. Verify PostgreSQL data
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT COUNT(*) FROM fact_trips_monthly;"
```

---

## 1. Service Health Checks

### Check All Services
```bash
docker compose ps
```

**Expected Output:** All services showing `Up` or `healthy`

### Check Individual Services

```bash
# Zookeeper
docker compose exec zookeeper nc -z localhost 2181 && echo "✅ Zookeeper OK" || echo "❌ Zookeeper FAILED"

# Kafka
docker compose exec kafka nc -z localhost 9092 && echo "✅ Kafka OK" || echo "❌ Kafka FAILED"

# HDFS NameNode
curl -s http://localhost:9870/jmx > /dev/null && echo "✅ HDFS NameNode OK" || echo "❌ HDFS FAILED"

# Spark Master
curl -s http://localhost:8080 > /dev/null && echo "✅ Spark Master OK" || echo "❌ Spark FAILED"

# PostgreSQL
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT 1;" > /dev/null && echo "✅ PostgreSQL OK" || echo "❌ PostgreSQL FAILED"

# Airflow
curl -s http://localhost:8083/health > /dev/null && echo "✅ Airflow OK" || echo "❌ Airflow FAILED"
```

### View Service Logs
```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f airflow-webserver
docker compose logs -f spark-master
docker compose logs -f kafka
docker compose logs -f postgres
```

---

## 2. Test Batch Pipeline (Primary)

### Step 1: Access Airflow UI
1. Open browser: http://localhost:8083
2. Login: `airflow` / `airflow`
3. Find DAG: `nyc_taxi_batch`
4. Toggle switch to **ON** (unpause)

### Step 2: Trigger DAG Manually
1. Click on `nyc_taxi_batch`
2. Click the **Play** button (▶) in top-right
3. Select **Trigger DAG**
4. Click **Trigger**

### Step 3: Monitor Execution
Watch the DAG run in Graph view:
- **Green** = Success ✅
- **Red** = Failed ❌
- **Yellow** = Running 🟡

**Expected Duration:** 10-15 minutes

### Step 4: Verify Each Task Completed
Click on each task to view logs:
- `prepare_dirs` ✅
- `download_dataset` ✅
- `spark_bronze` ✅
- `spark_silver` ✅
- `spark_gold` ✅

---

## 3. Verify HDFS Data

### Check Bronze Layer (Raw Data)
```bash
# List Bronze layer
docker compose exec namenode hdfs dfs -ls /datalake/nyc/bronze/yellow_tripdata

# Check file count
docker compose exec namenode hdfs dfs -count /datalake/nyc/bronze/yellow_tripdata

# View sample data (first 10 lines)
docker compose exec namenode hdfs dfs -cat /datalake/nyc/bronze/yellow_tripdata/*.parquet | head -10
```

**Expected:** You should see parquet files partitioned by year/month

### Check Silver Layer (Cleaned Data)
```bash
# List Silver layer
docker compose exec namenode hdfs dfs -ls /datalake/nyc/silver/yellow_tripdata

# Check file count
docker compose exec namenode hdfs dfs -count /datalake/nyc/silver/yellow_tripdata
```

### Check Gold Layer (Aggregated KPIs)
```bash
# List Gold layer
docker compose exec namenode hdfs dfs -ls /datalake/nyc/gold/kpis_trips_monthly

# Check file count
docker compose exec namenode hdfs dfs -count /datalake/nyc/gold/kpis_trips_monthly
```

### Check HDFS Storage Usage
```bash
# Check overall HDFS usage
docker compose exec namenode hdfs dfs -df -h

# Check specific directory usage
docker compose exec namenode hdfs dfs -du -h /datalake/nyc
```

---

## 4. Verify PostgreSQL Data

### Connect to PostgreSQL
```bash
docker compose exec -T postgres psql -U nyc -d nyc
```

### Check Tables Exist
```sql
-- List all tables
\dt

-- Expected tables:
-- batch_clean
-- taxi_zone_lookup
-- fact_trips_monthly
-- dq_results
-- job_runs
-- metrics_pipeline_runs
```

### Check Data in fact_trips_monthly
```sql
-- Count rows
SELECT COUNT(*) FROM fact_trips_monthly;

-- View latest data
SELECT * FROM fact_trips_monthly
ORDER BY year DESC, month DESC
LIMIT 10;

-- Check aggregates
SELECT
    year,
    month,
    total_trips,
    total_fare_amount,
    total_tip_amount,
    avg_trip_distance
FROM fact_trips_monthly
ORDER BY year DESC, month DESC;
```

### Check Data Quality Results
```sql
-- View DQ check results
SELECT * FROM dq_results
ORDER BY check_timestamp DESC
LIMIT 5;

-- Check if any DQ checks failed
SELECT * FROM dq_results
WHERE status = 'FAILED';
```

### Check Job Execution History
```sql
-- View recent job runs
SELECT * FROM job_runs
ORDER BY start_time DESC
LIMIT 10;

-- Check for failed jobs
SELECT * FROM job_runs
WHERE status = 'FAILED';
```

### Check Pipeline Metrics
```sql
-- View pipeline performance metrics
SELECT * FROM metrics_pipeline_runs
ORDER BY execution_date DESC
LIMIT 10;
```

### Exit PostgreSQL
```sql
\q
```

---

## 5. Test Streaming Pipeline (Alternative)

### Step 1: Verify Kafka is Running
```bash
# Check Kafka broker
docker compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# List topics
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Step 2: Trigger Kafka DAG
1. In Airflow UI, find: `nyc_taxi_kafka_batch`
2. Toggle to **ON**
3. Click **Trigger DAG**

### Step 3: Monitor Kafka Topic
```bash
# View messages in trips_raw topic (latest 10)
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic trips_raw \
  --from-beginning \
  --max-messages 10
```

### Step 4: Check Topic Details
```bash
# Describe trips_raw topic
docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe \
  --topic trips_raw
```

**Expected Output:**
- Topic: trips_raw
- Partition count: 3
- Replication factor: 1

### Step 5: Verify Data Flow
```bash
# Check consumer groups
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list
```

---

## 6. Access & Test Dashboards

### HDFS NameNode UI
```bash
open http://localhost:9870
```
- Browse filesystem
- Check DataNode status
- View cluster health

### Spark Master UI
```bash
open http://localhost:8080
```
- View running applications
- Check worker nodes
- View completed jobs

### Spark History Server
```bash
open http://localhost:18081
```
- View past Spark job logs
- Check execution times
- Debug failed jobs

### Adminer (Database UI)
```bash
open http://localhost:8082
```
- **Server:** postgres
- **Username:** nyc
- **Password:** nyc
- **Database:** nyc

Test SQL queries:
```sql
SELECT * FROM fact_trips_monthly LIMIT 10;
```

### Superset Setup & Test
```bash
# Initialize Superset (first time only)
docker compose exec superset superset db upgrade
docker compose exec superset superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@example.com \
  --password admin

docker compose exec superset superset init
```

Access Superset:
```bash
open http://localhost:8089
```
- Login: `admin` / `admin`
- Add Database: `postgresql://nyc:nyc@postgres:5432/nyc`
- Create charts and dashboards

---

## 7. Automated Testing Scripts

### Run All Verification Checks
```bash
./scripts/verify.sh
```

This script checks:
- ✅ All Docker containers running
- ✅ HDFS accessible
- ✅ Spark Master accessible
- ✅ PostgreSQL accepting connections
- ✅ Airflow UI accessible

### Run End-to-End Test
```bash
./scripts/run_e2e.sh
```

This script:
1. Triggers batch pipeline
2. Waits for completion
3. Validates data in HDFS
4. Validates data in PostgreSQL
5. Reports success/failure

---

## 8. Performance Testing

### Check Spark Job Performance
```bash
# View Spark event logs
docker compose exec spark-master ls /tmp/spark-events

# Check Spark worker resource usage
docker stats spark-master spark-worker-1
```

### Check HDFS Performance
```bash
# HDFS fsck (filesystem check)
docker compose exec namenode hdfs fsck / -files -blocks

# Check NameNode heap usage
docker compose exec namenode jps -lm
```

### Check PostgreSQL Performance
```sql
-- Connect to PostgreSQL
docker compose exec -T postgres psql -U nyc -d nyc

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check query performance
EXPLAIN ANALYZE SELECT * FROM fact_trips_monthly WHERE year = 2024;
```

### Monitor Resource Usage
```bash
# Check all container resource usage
docker stats

# Check specific service
docker stats spark-master postgres kafka
```

---

## 9. Data Validation Tests

### Validate Data Completeness
```bash
# Compare row counts: HDFS Bronze vs PostgreSQL Gold
echo "Bronze count:"
docker compose exec namenode hdfs dfs -cat /datalake/nyc/bronze/yellow_tripdata/*.parquet | wc -l

echo "PostgreSQL count:"
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT SUM(total_trips) FROM fact_trips_monthly;"
```

### Validate Data Quality
```sql
-- Check for NULL values
SELECT
    COUNT(*) FILTER (WHERE year IS NULL) as null_years,
    COUNT(*) FILTER (WHERE month IS NULL) as null_months,
    COUNT(*) FILTER (WHERE total_trips IS NULL) as null_trips
FROM fact_trips_monthly;

-- Check for negative values
SELECT COUNT(*)
FROM fact_trips_monthly
WHERE total_fare_amount < 0 OR total_tip_amount < 0;

-- Check for outliers
SELECT year, month, total_trips
FROM fact_trips_monthly
WHERE total_trips > (SELECT AVG(total_trips) * 3 FROM fact_trips_monthly)
ORDER BY total_trips DESC;
```

---

## 10. Troubleshooting Tests

### If Pipeline Fails

1. **Check Airflow Task Logs:**
   - Click on failed task in Airflow UI
   - View logs tab
   - Look for error messages

2. **Check Spark Logs:**
```bash
docker compose logs spark-master
docker compose logs spark-worker-1
```

3. **Check HDFS Logs:**
```bash
docker compose logs namenode
docker compose logs datanode
```

4. **Check PostgreSQL Logs:**
```bash
docker compose logs postgres
```

5. **Check Kafka Logs:**
```bash
docker compose logs kafka
docker compose logs zookeeper
```

### Test Network Connectivity
```bash
# Test inter-service communication
docker compose exec airflow-webserver ping -c 3 spark-master
docker compose exec spark-master ping -c 3 postgres
docker compose exec airflow-webserver ping -c 3 kafka
```

### Test Port Availability
```bash
# Check if ports are accessible
nc -zv localhost 9870  # HDFS
nc -zv localhost 8080  # Spark
nc -zv localhost 5432  # PostgreSQL
nc -zv localhost 9092  # Kafka
nc -zv localhost 8083  # Airflow
```

---

## Test Results Checklist

After running all tests, verify:

- [ ] All 11 Docker containers running
- [ ] HDFS accessible at http://localhost:9870
- [ ] Spark Master accessible at http://localhost:8080
- [ ] Airflow UI accessible at http://localhost:8083
- [ ] PostgreSQL accepting connections
- [ ] Kafka accepting connections
- [ ] Batch pipeline executes successfully (nyc_taxi_batch)
- [ ] Data visible in HDFS Bronze layer
- [ ] Data visible in HDFS Silver layer
- [ ] Data visible in HDFS Gold layer
- [ ] Data visible in PostgreSQL fact_trips_monthly
- [ ] Data quality checks passing
- [ ] No failed jobs in job_runs table
- [ ] Superset can connect to PostgreSQL
- [ ] Adminer can query database

---

## Quick Test Summary

### Minimal Smoke Test (2 minutes)
```bash
# 1. Check services
docker compose ps | grep -E "Up|healthy"

# 2. Check HDFS
curl -s http://localhost:9870/jmx > /dev/null && echo "✅ HDFS OK"

# 3. Check Spark
curl -s http://localhost:8080 > /dev/null && echo "✅ Spark OK"

# 4. Check PostgreSQL
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT 1;" && echo "✅ PostgreSQL OK"

# 5. Check Airflow
curl -s http://localhost:8083/health && echo "✅ Airflow OK"
```

### Full Pipeline Test (15 minutes)
```bash
# 1. Run verification script
./scripts/verify.sh

# 2. Trigger batch pipeline in Airflow UI
# http://localhost:8083

# 3. Wait 10-15 minutes for completion

# 4. Verify data in PostgreSQL
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT COUNT(*) FROM fact_trips_monthly;"

# 5. Check for errors
docker compose exec -T postgres psql -U nyc -d nyc -c "SELECT * FROM job_runs WHERE status = 'FAILED';"
```

---

## Need Help?

If tests fail:
1. Check the Troubleshooting section above
2. Review service logs: `docker compose logs [service-name]`
3. Ensure sufficient resources (16GB RAM, 50GB disk)
4. Try restarting services: `docker compose restart`
5. Full reset: `docker compose down -v && docker compose up -d`

**Happy Testing! 🚀**
