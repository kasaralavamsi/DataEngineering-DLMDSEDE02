#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "  DLMDSEDE02 Phase 3 – Docker Cleanup"
echo "========================================="
echo

# Step 1: Stop all running containers
echo "▶ Stopping all containers..."
docker compose down --remove-orphans 2>/dev/null || true

# Step 2: Remove project volumes
echo
echo "▶ Removing project volumes..."
docker compose down -v 2>/dev/null || true

# Step 3: Remove any dangling images
echo
echo "▶ Removing dangling images..."
docker image prune -f 2>/dev/null || true

# Step 4: Remove project-specific images (optional, controlled by flag)
if [[ "${1:-}" == "--full" ]]; then
  echo
  echo "▶ Full cleanup: removing project images..."
  docker rmi bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8 2>/dev/null || true
  docker rmi bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8 2>/dev/null || true
  docker rmi bde2020/spark-master:3.1.2-hadoop3.2 2>/dev/null || true
  docker rmi bde2020/spark-worker:3.1.2-hadoop3.2 2>/dev/null || true
  docker rmi bde2020/spark-history-server:3.1.2-hadoop3.2 2>/dev/null || true
  docker rmi postgres:15 2>/dev/null || true
  docker rmi adminer:4 2>/dev/null || true
  docker rmi bitnami/zookeeper:3.8 2>/dev/null || true
  docker rmi bitnami/kafka:3.4 2>/dev/null || true
  docker rmi apache/airflow:2.9.3-python3.11 2>/dev/null || true
  docker rmi apache/superset:3.1.0 2>/dev/null || true
  echo "   Images removed."
fi

# Step 5: Remove the project network
echo
echo "▶ Removing project network..."
docker network rm dlmdsede02_phase3_de-net 2>/dev/null || true

# Step 6: Show final state
echo
echo "========================================="
echo "  Cleanup complete!"
echo "========================================="
echo
echo "Remaining containers:"
docker ps -a --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null || echo "  (none)"
echo
echo "Remaining volumes:"
docker volume ls --format '{{.Name}}' | grep -i dlmdsede02 || echo "  (none related to this project)"
echo
echo "Usage:"
echo "  ./scripts/clean_docker.sh          # Stop containers + remove volumes"
echo "  ./scripts/clean_docker.sh --full   # Also remove all downloaded images"
