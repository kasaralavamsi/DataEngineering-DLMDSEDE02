
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum, avg as _avg, count as _count
from pyspark.sql.types import StructType, StructField, LongType, DoubleType
import argparse, uuid, time

# Gold KPI schema (written by nyc_silver_to_gold.py with partitionBy year/month).
# Providing an explicit schema avoids "Unable to infer schema" on empty parquet,
# and allows graceful handling when the gold path does not yet exist.
GOLD_SCHEMA = StructType([
    StructField("trips",        LongType(),   True),
    StructField("total_fare",   DoubleType(), True),
    StructField("total_tip",    DoubleType(), True),
    StructField("avg_distance", DoubleType(), True),
])

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--gold_base", required=True)
    p.add_argument("--jdbc_url", required=True)
    p.add_argument("--jdbc_user", required=True)
    p.add_argument("--jdbc_password", required=True)
    return p.parse_args()

def main():
    args = parse_args()
    spark = SparkSession.builder.appName("evaluate_gold_metrics").getOrCreate()

    gold_path = f"{args.gold_base}/kpis_trips_monthly"

    # Read gold KPIs; gracefully handle the case where the gold path does not
    # exist yet (nyc_silver_to_gold exits early when silver is empty, so gold
    # may be absent on the first pipeline run).
    try:
        df = (spark.read
              .schema(GOLD_SCHEMA)
              .option("mergeSchema", "true")
              .parquet(gold_path))
    except Exception as e:
        err = str(e)
        if "Path does not exist" in err or "Unable to infer schema" in err:
            print("⚠️  Gold path not found or empty — writing zero-value metrics row.")
            # Use spark.sql() to build the empty DataFrame in the JVM.
            # spark.createDataFrame([], schema) uses Python RDD serialization
            # via cloudpickle which is broken for PySpark 3.1.x on Python 3.11.
            df = spark.sql("""
                SELECT
                    CAST(NULL AS BIGINT) AS trips,
                    CAST(NULL AS DOUBLE) AS total_fare,
                    CAST(NULL AS DOUBLE) AS total_tip,
                    CAST(NULL AS DOUBLE) AS avg_distance
                WHERE 1 = 0
            """)
        else:
            raise

    months = int(df.select("year","month").distinct().count()) if "year" in df.columns else 0
    rows   = int(df.count())

    totals = df.agg(
        _sum("trips").alias("trips_total"),
        _sum("total_fare").alias("fare_total"),
        _sum("total_tip").alias("tip_total"),
        _avg("avg_distance").alias("avg_distance_over_months")
    ).collect()[0]

    trips_total_val  = float(totals["trips_total"]             or 0.0)
    fare_total_val   = float(totals["fare_total"]              or 0.0)
    tip_total_val    = float(totals["tip_total"]               or 0.0)
    avg_distance_val = float(totals["avg_distance_over_months"] or 0.0)

    run_id_val    = str(uuid.uuid4())
    run_epoch_val = int(time.time())

    # Use spark.sql() to build the single-row DataFrame entirely in the JVM.
    # This avoids Python-RDD serialization (cloudpickle) which is broken
    # for PySpark 3.1.x when running on Python 3.11.
    out_df = spark.sql(f"""
        SELECT
            '{run_id_val}'               AS run_id,
            CAST({run_epoch_val}         AS BIGINT)  AS run_epoch,
            CAST({months}               AS BIGINT)  AS months_covered,
            CAST({rows}                 AS BIGINT)  AS rows_gold,
            CAST({trips_total_val!r}    AS DOUBLE)  AS trips_total,
            CAST({fare_total_val!r}     AS DOUBLE)  AS fare_total,
            CAST({tip_total_val!r}      AS DOUBLE)  AS tip_total,
            CAST({avg_distance_val!r}   AS DOUBLE)  AS avg_distance_over_months
    """)

    (out_df.write
        .format("jdbc")
        .option("url", args.jdbc_url)
        .option("dbtable", "public.metrics_pipeline_runs")
        .option("user", args.jdbc_user)
        .option("password", args.jdbc_password)
        .option("driver", "org.postgresql.Driver")
        .mode("append")
        .save())

    print("Run metrics written to public.metrics_pipeline_runs")
    spark.stop()

if __name__ == "__main__":
    main()
