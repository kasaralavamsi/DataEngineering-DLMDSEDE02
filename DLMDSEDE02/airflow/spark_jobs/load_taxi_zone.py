"""
load_taxi_zone.py
─────────────────
Downloads the NYC TLC taxi zone lookup CSV and upserts it into
Postgres public.taxi_zone_lookup.

Why psycopg2 instead of spark.createDataFrame() + JDBC
───────────────────────────────────────────────────────
PySpark 3.1.2 runs on Python 3.11 in this container.  Whenever PySpark
needs to ship Python objects to executors it serialises them via the
bundled cloudpickle (v1.6.0).  That version cannot parse Python 3.11
bytecode (the ``names[oparg]`` index is out of range) so ANY path through
spark.createDataFrame(python_list) fails with:

    _pickle.PicklingError: Could not serialize object: IndexError: tuple
    index out of range

For a 265-row lookup table there is no value in involving Spark at all.
We keep a minimal SparkSession so spark-submit is satisfied, then write
directly to Postgres with psycopg2 — zero cloudpickle involvement.
"""
import argparse, csv, io, urllib.request, urllib.parse
from pyspark.sql import SparkSession

ZONE_CSV_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--jdbc_url",      default="jdbc:postgresql://postgres:5432/nyc")
    p.add_argument("--jdbc_user",     default="nyc")
    p.add_argument("--jdbc_password", default="nyc")
    return p.parse_args()


def main():
    args = parse_args()

    # Minimal SparkSession — required when launched via spark-submit,
    # but we don't use any Spark DataFrame operations here.
    spark = (SparkSession.builder
             .appName("load_taxi_zone_lookup")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")

    # ── 1. Download and parse CSV entirely in Python (driver only) ────────────
    print(f"Downloading {ZONE_CSV_URL} …")
    with urllib.request.urlopen(ZONE_CSV_URL) as resp:
        content = resp.read().decode("utf-8")

    rows = []
    for record in csv.DictReader(io.StringIO(content)):
        rows.append((
            int(record["LocationID"]),
            record["Borough"],
            record["Zone"],
            record["service_zone"],
        ))
    print(f"Parsed {len(rows)} taxi zone rows")

    # ── 2. Write to Postgres with psycopg2 (no Spark serialisation) ───────────
    # Parse host/port/dbname from the JDBC URL
    # Format: jdbc:postgresql://host:port/dbname
    pg_url  = args.jdbc_url[len("jdbc:"):]          # strip "jdbc:" prefix
    parsed  = urllib.parse.urlparse(pg_url)
    db_host = parsed.hostname
    db_port = parsed.port or 5432
    db_name = parsed.path.lstrip("/")

    import psycopg2
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=args.jdbc_user,
        password=args.jdbc_password,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE public.taxi_zone_lookup RESTART IDENTITY")
            cur.executemany(
                """INSERT INTO public.taxi_zone_lookup
                       (location_id, borough, zone, service_zone)
                   VALUES (%s, %s, %s, %s)""",
                rows,
            )
        conn.commit()
        print(f"Inserted {len(rows)} rows into public.taxi_zone_lookup")
    finally:
        conn.close()

    spark.stop()


if __name__ == "__main__":
    main()
