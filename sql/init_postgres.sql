<<<<<<< HEAD
-- =============================================================
-- PostgreSQL Init Script – Phase 3
-- Creates all tables used by the pipeline
-- =============================================================

-- Phase 2 batch_clean table (Spark job writes cleaned zone data)
=======
-- Create an extension/schema if you want, not required.
>>>>>>> 778e3e725a2aa2d44da11823497b0d8da72a3ccd
CREATE TABLE IF NOT EXISTS public.batch_clean (
  LocationID   INT,
  Borough      TEXT,
  Zone         TEXT,
  service_zone TEXT,
  loaded_at    TIMESTAMPTZ DEFAULT now()
<<<<<<< HEAD
);

-- Taxi zone lookup reference table (loaded by load_taxi_zone.py)
CREATE TABLE IF NOT EXISTS public.taxi_zone_lookup (
  LocationID   INT PRIMARY KEY,
  Borough      TEXT,
  Zone         TEXT,
  service_zone TEXT
);

-- Gold layer: monthly trip KPIs (written by nyc_silver_to_gold.py)
CREATE TABLE IF NOT EXISTS public.fact_trips_monthly (
  year         INT,
  month        INT,
  trips        BIGINT,
  total_fare   NUMERIC(14,2),
  total_tip    NUMERIC(14,2),
  avg_distance NUMERIC(10,2),
  PRIMARY KEY (year, month)
);

-- Data quality check results (written by dq_check_silver.py)
CREATE TABLE IF NOT EXISTS public.dq_results (
  run_id             TEXT PRIMARY KEY,
  run_epoch          BIGINT,
  rows_total         BIGINT,
  null_trip_distance BIGINT,
  null_fare_amount   BIGINT,
  bad_distance       BIGINT,
  bad_fare           BIGINT,
  rate_null_distance DOUBLE PRECISION,
  rate_null_fare     DOUBLE PRECISION,
  rate_bad_distance  DOUBLE PRECISION,
  rate_bad_fare      DOUBLE PRECISION,
  passed             INT
);

-- Pipeline run metrics (written by evaluate_gold_metrics.py)
CREATE TABLE IF NOT EXISTS public.metrics_pipeline_runs (
  run_id                    TEXT PRIMARY KEY,
  run_epoch                 BIGINT,
  months_covered            INT,
  rows_gold                 BIGINT,
  trips_total               DOUBLE PRECISION,
  fare_total                DOUBLE PRECISION,
  tip_total                 DOUBLE PRECISION,
  avg_distance_over_months  DOUBLE PRECISION
);
=======
);
>>>>>>> 778e3e725a2aa2d44da11823497b0d8da72a3ccd
