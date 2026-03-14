#!/usr/bin/env bash
set -euo pipefail
mkdir -p jars
JAR="jars/postgresql-42.6.0.jar"
if [[ ! -f "$JAR" ]]; then
  echo "Downloading PostgreSQL JDBC 42.6.0 ..."
  curl -L -o "$JAR" https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar
else
  echo "Found $JAR"
fi
