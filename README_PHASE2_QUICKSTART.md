# Phase 2 – One-click Stack + Batch Job

## Prereqs
- Docker Desktop running
- macOS on Apple Silicon ok (we pin linux/amd64 images)
- Internet (first run will pull images and the Postgres JDBC jar)

## Files
- `docker-compose.yml` – Hadoop (HDFS), Spark (master+worker), Postgres, HDFS bootstrap
- `app/spark_job.py` – Reads CSV from HDFS and writes to Postgres (table `public.batch_clean`)
- `scripts/run_e2e.sh` – Runs the whole flow end-to-end
- `scripts/download_jdbc.sh` – Fetches the Postgres JDBC driver into `./jars/`

## Quickstart (4 commands)
```bash
git clone <your repo> && cd <your folder>  # or unzip this pack
chmod +x scripts/*.sh
docker compose up -d                        # start stack once
./scripts/run_e2e.sh                        # boot HDFS + submit Spark + verify Postgres
```

If you want to re-run cleanly:
```bash
docker compose down -v
docker compose up -d
./scripts/run_e2e.sh
```

## Verify manually
- HDFS UI: http://localhost:9870
- Spark Master UI: http://localhost:8080
- Postgres: `docker exec -it $(docker ps --format '{{.Names}}' | grep postgres) psql -U nyc -d nyc -c "SELECT COUNT(*) FROM public.batch_clean;"`
