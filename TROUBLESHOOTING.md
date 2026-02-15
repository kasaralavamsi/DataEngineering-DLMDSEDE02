# Troubleshooting Guide

Common issues and solutions for the NYC Taxi Data Engineering Pipeline.

---

## 🐳 Docker Issues

### Error: "docker-credential-desktop: executable file not found"

**Symptom:**
```bash
error getting credentials - err: exec: "docker-credential-desktop": executable file not found in $PATH
```

**Cause:** Docker is configured to use Docker Desktop's credential helper, but it's not in your system PATH.

**Solution 1 - Quick Fix (Recommended):**
```bash
# Run the fix script
./scripts/fix_docker_credentials.sh
```

**Solution 2 - Manual Fix:**
```bash
# Create Docker config directory
mkdir -p ~/.docker

# Create clean config
cat > ~/.docker/config.json << 'EOF'
{
  "auths": {},
  "currentContext": "default"
}
EOF

# Verify
cat ~/.docker/config.json
```

**Solution 3 - Edit Existing Config:**
```bash
# Backup existing config
cp ~/.docker/config.json ~/.docker/config.json.backup

# Edit and remove the "credsStore" line
nano ~/.docker/config.json
```

Remove or comment out:
```json
"credsStore": "desktop",
```

---

### Error: Cannot connect to Docker daemon

**Symptom:**
```bash
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solution:**
```bash
# Check if Docker Desktop is running
docker ps

# If not, start Docker Desktop from Applications
# Then verify:
docker --version
docker compose version
```

---

### Error: Port already in use

**Symptom:**
```bash
Error starting userland proxy: listen tcp4 0.0.0.0:8080: bind: address already in use
```

**Solution:**
```bash
# Find what's using the port (example: port 8080)
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or stop all containers and restart
docker compose down
docker compose up -d
```

---

## 🔧 Container Issues

### Containers keep restarting

**Check container logs:**
```bash
# View specific container logs
docker logs <container-name>

# Follow logs in real-time
docker logs -f <container-name>

# View last 50 lines
docker logs --tail 50 <container-name>
```

**Common container names:**
- `namenode`, `datanode` (HDFS)
- `postgres` (Database)
- `spark-master`, `spark-worker-1` (Spark)
- `airflow-webserver`, `airflow-scheduler` (Airflow)
- `kafka`, `zookeeper` (Streaming)

---

### HDFS NameNode not starting

**Solution:**
```bash
# Check if namenode volume is corrupted
docker compose down -v  # WARNING: This deletes all data
docker compose up -d

# Or just reset namenode
docker volume rm <project>_hdfs-namenode
docker compose up -d
```

---

### Airflow database migration errors

**Solution:**
```bash
# Reset Airflow database
docker compose stop airflow-webserver airflow-scheduler airflow-init
docker volume rm <project>_airflow-pgdata
docker compose up -d
```

---

## 🗄️ Database Issues

### PostgreSQL connection refused

**Check if PostgreSQL is healthy:**
```bash
docker compose ps postgres

# Should show: (healthy)
# If not, check logs:
docker logs postgres
```

**Connect manually:**
```bash
docker exec -it postgres psql -U nyc -d nyc

# List tables
\dt

# Exit
\q
```

---

### Missing tables in PostgreSQL

**Solution:**
```bash
# Check if init scripts ran
docker logs postgres | grep "init"

# Manually run init scripts
docker exec -i postgres psql -U nyc -d nyc < sql/init_postgres.sql
docker exec -i postgres psql -U nyc -d nyc < sql/init_phase3_metrics.sql
```

---

## ⚡ Spark Issues

### Spark jobs failing with memory errors

**Solution 1 - Increase memory:**

Edit `docker-compose.yml`:
```yaml
spark-worker-1:
  environment:
    - SPARK_WORKER_MEMORY=2g  # Increase from default
```

**Solution 2 - Check Spark logs:**
```bash
# View Spark Master logs
docker logs spark-master

# View Worker logs
docker logs spark-worker-1

# View Spark UI
# Open: http://localhost:8080
```

---

## 🌊 Airflow Issues

### DAGs not appearing in Airflow UI

**Check DAG directory:**
```bash
# List DAGs in container
docker exec -it airflow-webserver ls -la /opt/airflow/dags

# Check Airflow DAG list
docker exec -it airflow-webserver airflow dags list
```

**Solution:**
```bash
# Restart scheduler
docker compose restart airflow-scheduler

# Force DAG refresh
docker exec -it airflow-webserver airflow dags list-import-errors
```

---

### Airflow login not working

**Default credentials:**
- Username: `airflow`
- Password: `airflow`

**Reset admin user:**
```bash
docker exec -it airflow-webserver airflow users create \
  --role Admin \
  --username admin \
  --password admin \
  --email admin@example.com \
  --firstname Admin \
  --lastname User
```

---

## 📊 Data Pipeline Issues

### No data in HDFS

**Check HDFS:**
```bash
# List HDFS contents
docker exec -it namenode hdfs dfs -ls /data/raw

# Upload data manually
docker exec -it namenode hdfs dfs -put /data/reference/*.csv /data/raw/
```

---

### Data quality checks failing

**View DQ results:**
```bash
docker exec -it postgres psql -U nyc -d nyc -c "SELECT * FROM dq_results ORDER BY run_epoch DESC LIMIT 5;"
```

---

## 🧹 Clean Slate (Nuclear Option)

If all else fails, completely reset the environment:

```bash
# Stop all containers
docker compose down

# Remove all volumes (⚠️ DELETES ALL DATA)
docker compose down -v

# Remove unused images
docker system prune -a

# Start fresh
docker compose up -d

# Wait for all services to be healthy
watch docker compose ps
```

---

## 🔍 Verification Commands

After fixing issues, verify everything is working:

```bash
# Run verification script
./scripts/verify.sh

# Check all containers are running
docker compose ps

# Check service health
curl http://localhost:8083/health  # Airflow
curl http://localhost:8088/health  # Superset
curl http://localhost:9870/jmx     # HDFS
```

---

## 📚 Useful Commands

### Docker Compose
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Restart a service
docker compose restart <service-name>

# Check status
docker compose ps
```

### Resource Management
```bash
# Check disk usage
docker system df

# Clean up unused resources
docker system prune

# View container resource usage
docker stats
```

---

## 🆘 Getting Help

If you encounter issues not covered here:

1. **Check logs:** `docker compose logs -f <service>`
2. **Check health:** `docker compose ps`
3. **Search issues:** [GitHub Repository Issues](https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02/issues)
4. **Documentation:** See README.md for detailed setup instructions

---

## 📞 Contact

**Project:** DLMDSEDE02 Data Engineering
**Student:** Vamshi Krishna Kasarala (92202958)
**Repository:** https://github.com/kasaralavamsi/DataEngineering-DLMDSEDE02
