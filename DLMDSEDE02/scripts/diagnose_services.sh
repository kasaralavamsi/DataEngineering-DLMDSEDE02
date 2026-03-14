#!/usr/bin/env bash
# =============================================================================
# Service Diagnostics Script
# Check health and connectivity of all services
# =============================================================================

set -e

echo "🔍 NYC Taxi Pipeline - Service Diagnostics"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker compose is running
echo "📦 Checking Docker Compose Status..."
echo ""
docker compose ps
echo ""

# Function to check service health
check_service() {
    local service=$1
    local port=$2
    local url=$3

    echo -n "🔍 ${service} (port ${port}): "

    # Check if container is running
    if docker compose ps | grep -q "${service}.*Up"; then
        echo -e "${GREEN}Container Running${NC}"

        # Check if port is accessible
        if nc -z localhost ${port} 2>/dev/null; then
            echo "   ✅ Port ${port} is accessible"

            # Try HTTP endpoint if provided
            if [ -n "${url}" ]; then
                if curl -s -f "${url}" > /dev/null 2>&1; then
                    echo "   ✅ HTTP endpoint responding"
                else
                    echo -e "   ${YELLOW}⚠️  HTTP endpoint not responding yet${NC}"
                fi
            fi
        else
            echo -e "   ${RED}❌ Port ${port} NOT accessible${NC}"
        fi
    else
        echo -e "${RED}Container NOT Running${NC}"
        echo "   Run: docker logs ${service}"
    fi
    echo ""
}

# Check PostgreSQL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️  POSTGRESQL SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_service "postgres" "5432" ""

# Try to connect to PostgreSQL
echo "Testing PostgreSQL connection..."
POSTGRES_CONTAINER=$(docker ps --format '{{.Names}}' | grep postgres | grep -v airflow | head -1)
if [ -n "$POSTGRES_CONTAINER" ]; then
    if docker exec "$POSTGRES_CONTAINER" psql -U nyc -d nyc -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ PostgreSQL connection successful${NC}"
        echo ""
        echo "   Connection Details:"
        echo "   - Host: localhost"
        echo "   - Port: 5432"
        echo "   - User: nyc"
        echo "   - Password: nyc"
        echo "   - Database: nyc"
        echo ""
        echo "   Adminer UI: http://localhost:8082"
        echo "   - Server: postgres"
        echo "   - Username: nyc"
        echo "   - Password: nyc"
        echo "   - Database: nyc"
    else
        echo -e "   ${RED}❌ PostgreSQL connection failed${NC}"
        echo "   Run: docker logs postgres"
    fi
else
    echo -e "   ${YELLOW}⚠️  PostgreSQL not healthy yet. Waiting for initialization...${NC}"
    echo "   This can take 30-60 seconds on first startup."
fi
echo ""

# Check Kafka
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📨 KAFKA SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_service "kafka" "9092" ""
check_service "zookeeper" "2181" ""

# Try to connect to Kafka
echo "Testing Kafka connection..."
KAFKA_CONTAINER=$(docker ps --format '{{.Names}}' | grep kafka | head -1)
if [ -n "$KAFKA_CONTAINER" ]; then
    if docker exec "$KAFKA_CONTAINER" kafka-topics --list --bootstrap-server localhost:9092 > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Kafka broker accessible${NC}"
        echo ""
        echo "   Connection Details:"
        echo "   - Bootstrap Server: localhost:9092"
        echo ""
        echo "   List topics:"
        echo "   docker exec kafka kafka-topics --list --bootstrap-server localhost:9092"
    else
        echo -e "   ${RED}❌ Kafka broker not accessible${NC}"
        echo "   Run: docker logs kafka"
        echo "   Run: docker logs zookeeper"
    fi
else
    echo -e "   ${YELLOW}⚠️  Kafka not running${NC}"
fi
echo ""

# Check other critical services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 OTHER SERVICES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_service "namenode" "9870" "http://localhost:9870/jmx"
check_service "spark-master" "8080" ""
check_service "airflow-webserver" "8083" "http://localhost:8083/health"
check_service "superset" "8089" "http://localhost:8088/health"

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL=$(docker compose ps | grep -c "Up" || echo "0")
HEALTHY=$(docker compose ps | grep -c "healthy" || echo "0")

echo "Total containers running: ${TOTAL}"
echo "Healthy containers: ${HEALTHY}"
echo ""

if [ "$HEALTHY" -lt "4" ]; then
    echo -e "${YELLOW}⚠️  Some services are still starting up.${NC}"
    echo "   Wait 1-2 minutes and run this script again."
    echo ""
    echo "   To watch status in real-time:"
    echo "   watch -n 2 'docker compose ps'"
else
    echo -e "${GREEN}✅ Most services are healthy!${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 TROUBLESHOOTING COMMANDS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "View logs for a service:"
echo "  docker logs postgres"
echo "  docker logs kafka"
echo "  docker logs <service-name>"
echo ""
echo "Restart a service:"
echo "  docker compose restart postgres"
echo "  docker compose restart kafka"
echo ""
echo "Check if ports are in use:"
echo "  lsof -i :5432  # PostgreSQL"
echo "  lsof -i :9092  # Kafka"
echo ""
echo "Full reset (⚠️  deletes data):"
echo "  docker compose down -v"
echo "  docker compose up -d"
echo ""
