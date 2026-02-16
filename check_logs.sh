#!/bin/bash
echo "🔍 Checking PostgreSQL logs..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker logs dlmdsede02_phase3-postgres-1 2>&1 | tail -20
echo ""
echo "🔍 Checking Kafka logs..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker logs dlmdsede02_phase3-kafka-1 2>&1 | tail -20
