-- =============================================================
-- Job tracking table
-- =============================================================

CREATE TABLE IF NOT EXISTS public.job_runs (
  id           BIGSERIAL PRIMARY KEY,
  job_name     TEXT NOT NULL,
  started_at   TIMESTAMPTZ DEFAULT now(),
  finished_at  TIMESTAMPTZ,
  status       TEXT,
  rows_written BIGINT
);

-- Create indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_dq_results_run_epoch ON public.dq_results (run_epoch);
CREATE INDEX IF NOT EXISTS idx_metrics_run_epoch ON public.metrics_pipeline_runs (run_epoch);
CREATE INDEX IF NOT EXISTS idx_fact_trips_year_month ON public.fact_trips_monthly (year, month);
