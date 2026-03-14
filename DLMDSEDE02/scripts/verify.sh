#!/usr/bin/env bash
set -euo pipefail

# Helper to grab container name by substring
get_c() { docker ps --format '{{.Names}}' | grep -m1 "$1"; }

NN=$(get_c namenode || true)
DN=$(get_c datanode || true)
KF=$(get_c kafka || true)
ZK=$(get_c zookeeper || true)
PG=$(get_c "postgres" | grep -v airflow || true)
SM=$(get_c spark-master || true)
AW=$(get_c airflow-webserver || true)

echo "== Docker containers =="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

echo
echo "== HDFS check =="
if [[ -n "${NN}" ]]; then
  docker exec -it "$NN" bash -lc 'hdfs dfs -mkdir -p /tmp && hdfs dfs -ls /data/raw'
else
  echo "WARN: namenode not found"
fi

echo
echo "== Kafka topic create/list =="
if [[ -n "${KF}" ]]; then
  docker exec -it "$KF" bash -lc "/opt/bitnami/kafka/bin/kafka-topics.sh \
    --create --if-not-exists --topic trips_raw \
    --partitions 1 --replication-factor 1 --bootstrap-server localhost:9092 && \
    /opt/bitnami/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092"
else
  echo "WARN: kafka not found"
fi

echo
echo "== Postgres tables =="
if [[ -n "${PG}" ]]; then
  docker exec -it "$PG" psql -U nyc -d nyc -c '\dt'
else
  echo "WARN: postgres not found"
fi

echo
echo "== Spark test (with JDBC driver) =="
if [[ -n "${SM}" ]]; then
  docker exec -it "$SM" bash -lc '
    test -f /opt/spark/app/spark_job.py && \
    spark-submit --packages org.postgresql:postgresql:42.6.0 /opt/spark/app/spark_job.py || \
    echo "No spark_job.py found; skipping."'
else
  echo "WARN: spark-master not found"
fi

echo
echo "== Airflow DAGs =="
if [[ -n "${AW}" ]]; then
  docker exec -it "$AW" bash -lc 'airflow dags list | head -n 20'
else
  echo "WARN: airflow-webserver not found"
fi

echo
echo "All checks attempted."
