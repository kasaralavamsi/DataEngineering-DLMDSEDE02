
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum, avg as _avg, count as _count, round as _round
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType,
    TimestampType, DateType
)
import argparse

# Mirrors the output schema of nyc_bronze_to_silver.py (silver stage).
# Providing an explicit schema prevents the "Unable to infer schema" error when
# the silver path exists but contains no Parquet files yet (e.g. the first
# pipeline run where Kafka→bronze→silver hasn't produced data yet).
SILVER_SCHEMA = StructType([
    StructField("VendorID",               DoubleType(),    True),
    StructField("tpep_pickup_datetime",   TimestampType(), True),
    StructField("tpep_dropoff_datetime",  TimestampType(), True),
    StructField("passenger_count",        DoubleType(),    True),
    StructField("trip_distance",          DoubleType(),    True),
    StructField("RatecodeID",             DoubleType(),    True),
    StructField("store_and_fwd_flag",     StringType(),    True),
    StructField("PULocationID",           DoubleType(),    True),
    StructField("DOLocationID",           DoubleType(),    True),
    StructField("payment_type",           DoubleType(),    True),
    StructField("fare_amount",            DoubleType(),    True),
    StructField("extra",                  DoubleType(),    True),
    StructField("mta_tax",               DoubleType(),    True),
    StructField("tip_amount",             DoubleType(),    True),
    StructField("tolls_amount",           DoubleType(),    True),
    StructField("improvement_surcharge",  DoubleType(),    True),
    StructField("total_amount",           DoubleType(),    True),
    StructField("congestion_surcharge",   DoubleType(),    True),
    StructField("airport_fee",            DoubleType(),    True),
    StructField("pickup_date",            DateType(),      True),
    StructField("year",                   IntegerType(),   True),
    StructField("month",                  IntegerType(),   True),
])


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--silver_base", required=True)
    p.add_argument("--gold_base", required=True)
    p.add_argument("--jdbc_url", required=True)
    p.add_argument("--jdbc_user", required=True)
    p.add_argument("--jdbc_password", required=True)
    return p.parse_args()

def main():
    args = parse_args()
    spark = (SparkSession.builder
             .appName("nyc_silver_to_gold")
             # Default shuffle.partitions=200 creates 200 tasks for every
             # GroupBy/repartition, which kills performance on a single-worker
             # cluster (and hits Airflow task timeouts).  4 is more than enough
             # for a handful of year/month KPI rows.
             .config("spark.sql.shuffle.partitions", "4")
             .getOrCreate())

    silver_path = f"{args.silver_base}/yellow_tripdata"

    # Use explicit schema so we never crash on an empty silver path.
    # mergeSchema is safe because every silver file shares the same schema.
    df = (spark.read
          .schema(SILVER_SCHEMA)
          .option("basePath", silver_path)
          .option("mergeSchema", "false")
          .parquet(silver_path))

    # Guard: if silver produced no rows yet, exit cleanly rather than writing
    # empty gold tables that would confuse downstream consumers.
    # NOTE: df.rdd.isEmpty() is intentionally avoided here — it triggers Python
    # RDD serialization via cloudpickle, which is broken for PySpark 3.1.x
    # running on Python 3.11 (cloudpickle cannot parse the new bytecode format).
    # df.limit(1).count() is a pure JVM operation with no Python serialization.
    if df.limit(1).count() == 0:
        print("⚠️  Silver path is empty — no data to aggregate. "
              "Re-run after the Kafka→bronze→silver pipeline has written data.")
        spark.stop()
        return

    kpis = (df.groupBy("year","month")
              .agg(
                   _count("*").alias("trips"),
                   _round(_sum("fare_amount"),2).alias("total_fare"),
                   _round(_sum("tip_amount"),2).alias("total_tip"),
                   _round(_avg("trip_distance"),2).alias("avg_distance")
              ))

    gold_path = f"{args.gold_base}/kpis_trips_monthly"
    # coalesce(1) avoids a second shuffle (repartition would trigger another
    # 4-way shuffle after the agg shuffle).  For a small KPI table (1 row per
    # month) this produces one parquet file per year/month Hive partition,
    # which is perfectly fine.
    (kpis.coalesce(1)
         .write.mode("overwrite")
         .partitionBy("year","month")
         .parquet(gold_path))
    print("Wrote gold KPIs to", gold_path)

    (kpis.select("year","month","trips","total_fare","total_tip","avg_distance")
         .write.format("jdbc")
         .option("url", args.jdbc_url)
         .option("dbtable", "public.fact_trips_monthly")
         .option("user", args.jdbc_user)
         .option("password", args.jdbc_password)
         .option("driver", "org.postgresql.Driver")
         .mode("overwrite")
         .save())
    print("Wrote fact_trips_monthly to Postgres")

    spark.stop()

if __name__ == "__main__":
    main()
