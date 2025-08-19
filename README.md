# NYC Taxi — Phase 2 + Phase 3 (All-In-One)
## Start
docker compose up -d
## Run
Airflow http://localhost:8088 → DAGs: nyc_taxi_batch (or nyc_taxi_kafka_batch), then nyc_phase3_eval
## Outputs
HDFS: /datalake/nyc/{bronze|silver|gold}; Postgres: fact_trips_monthly, dq_results, metrics_pipeline_runs
