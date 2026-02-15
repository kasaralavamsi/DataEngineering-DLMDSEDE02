-- Create an extension/schema if you want, not required.
CREATE TABLE IF NOT EXISTS public.batch_clean (
  LocationID   INT,
  Borough      TEXT,
  Zone         TEXT,
  service_zone TEXT,
  loaded_at    TIMESTAMPTZ DEFAULT now()
);