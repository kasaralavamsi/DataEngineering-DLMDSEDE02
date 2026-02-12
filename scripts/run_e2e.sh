#!/usr/bin/env bash
set -euo pipefail

echo "▶ (Re)starting all containers..."
docker compose up -d || true

echo "▶ Waiting for NameNode health..."
until docker compose ps | grep namenode | grep -q "(healthy)"; do sleep 2; done
echo "▶ Waiting for Postgres health..."
until docker compose ps | grep -w postgres | grep -q "(healthy)"; do sleep 2; done

NN=$(docker ps --format '{{.Names}}' | grep namenode)
SM=$(docker ps --format '{{.Names}}' | grep spark-master)

echo "▶ Bootstrapping HDFS path and CSV (idempotent)..."
docker exec -it "$NN" bash -lc '
  /opt/hadoop-3.2.1/bin/hdfs dfs -mkdir -p /data/raw
  if ls -1 /datasets/*.csv >/dev/null 2>&1; then
    /opt/hadoop-3.2.1/bin/hdfs dfs -put -f /datasets/*.csv /data/raw
  fi
  /opt/hadoop-3.2.1/bin/hdfs dfs -ls -h /data/raw || true
'

echo "▶ Submitting Spark job (will auto-fetch JDBC driver)..."
docker exec -it "$SM" bash -lc '
  /spark/bin/spark-submit \
    --packages org.postgresql:postgresql:42.6.0 \
    /opt/spark/app/spark_job.py
'

echo "▶ Verifying row count in Postgres..."
PG=$(docker ps --format "{{.Names}}" | grep -w postgres | grep -v airflow)
docker exec -it "$PG" psql -U nyc -d nyc -c "SELECT COUNT(*) AS rows FROM public.batch_clean;"
echo "✅ Done."
