-- ============================================================
-- Phase 3 — Additional indexes and helper views
-- ============================================================

-- Convenience view: latest DQ check result
CREATE OR REPLACE VIEW public.v_latest_dq AS
SELECT *
FROM public.dq_results
ORDER BY run_epoch DESC
LIMIT 1;

-- Convenience view: latest pipeline run metrics
CREATE OR REPLACE VIEW public.v_latest_metrics AS
SELECT *
FROM public.metrics_pipeline_runs
ORDER BY run_epoch DESC
LIMIT 1;
