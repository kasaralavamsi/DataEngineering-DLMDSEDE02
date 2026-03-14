-- ============================================================
-- NYC Taxi Data Warehouse — Initial Schema
-- ============================================================

-- Gold layer KPIs (written by nyc_silver_to_gold.py via JDBC overwrite)
CREATE TABLE IF NOT EXISTS public.fact_trips_monthly (
    year          INTEGER,
    month         INTEGER,
    trips         BIGINT,
    total_fare    DOUBLE PRECISION,
    total_tip     DOUBLE PRECISION,
    avg_distance  DOUBLE PRECISION,
    PRIMARY KEY (year, month)
);

-- Data quality results (written by dq_check_silver.py via JDBC append)
CREATE TABLE IF NOT EXISTS public.dq_results (
    run_id              TEXT,
    run_epoch           BIGINT,
    rows_total          BIGINT,
    null_trip_distance  BIGINT,
    null_fare_amount    BIGINT,
    bad_distance        BIGINT,
    bad_fare            BIGINT,
    rate_null_distance  DOUBLE PRECISION,
    rate_null_fare      DOUBLE PRECISION,
    rate_bad_distance   DOUBLE PRECISION,
    rate_bad_fare       DOUBLE PRECISION,
    passed              INTEGER
);

-- Pipeline run metrics (written by evaluate_gold_metrics.py via JDBC append)
CREATE TABLE IF NOT EXISTS public.metrics_pipeline_runs (
    run_id                   TEXT,
    run_epoch                BIGINT,
    months_covered           BIGINT,
    rows_gold                BIGINT,
    trips_total              DOUBLE PRECISION,
    fare_total               DOUBLE PRECISION,
    tip_total                DOUBLE PRECISION,
    avg_distance_over_months DOUBLE PRECISION
);

-- Reference: NYC taxi zone lookup (loaded by load_taxi_zone_lookup_daily DAG)
CREATE TABLE IF NOT EXISTS public.taxi_zone_lookup (
    location_id   INTEGER PRIMARY KEY,
    borough       TEXT,
    zone          TEXT,
    service_zone  TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_fact_trips_year_month  ON public.fact_trips_monthly (year, month);
CREATE INDEX IF NOT EXISTS idx_dq_results_run_epoch   ON public.dq_results (run_epoch);
CREATE INDEX IF NOT EXISTS idx_metrics_run_epoch      ON public.metrics_pipeline_runs (run_epoch);
