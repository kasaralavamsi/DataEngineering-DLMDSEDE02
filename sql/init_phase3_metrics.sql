CREATE TABLE IF NOT EXISTS public.metrics_pipeline_runs (
  run_id text PRIMARY KEY, run_epoch bigint, months_covered int, rows_gold bigint,
  trips_total numeric, fare_total numeric, tip_total numeric, avg_distance_over_months numeric);
CREATE TABLE IF NOT EXISTS public.dq_results (
  run_id text PRIMARY KEY, run_epoch bigint, rows_total bigint,
  null_trip_distance bigint, null_fare_amount bigint, bad_distance bigint, bad_fare bigint,
  rate_null_distance numeric, rate_null_fare numeric, rate_bad_distance numeric, rate_bad_fare numeric, passed int);
