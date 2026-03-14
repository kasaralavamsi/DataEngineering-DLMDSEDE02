
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType, DateType,
)
import argparse, time, uuid

# Silver schema mirrors BRONZE_SCHEMA in nyc_bronze_to_silver.py plus the
# derived pickup_date column.  Providing an explicit schema avoids Spark's
# "Unable to infer schema for Parquet" error when the directory contains
# empty partition files (which can occur after a first run that wrote 0 rows).
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
    StructField("mta_tax",                DoubleType(),    True),
    StructField("tip_amount",             DoubleType(),    True),
    StructField("tolls_amount",           DoubleType(),    True),
    StructField("improvement_surcharge",  DoubleType(),    True),
    StructField("total_amount",           DoubleType(),    True),
    StructField("congestion_surcharge",   DoubleType(),    True),
    StructField("airport_fee",            DoubleType(),    True),
    StructField("pickup_date",            DateType(),      True),
])

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--silver_base", required=True)
    p.add_argument("--jdbc_url", required=True)
    p.add_argument("--jdbc_user", required=True)
    p.add_argument("--jdbc_password", required=True)
    return p.parse_args()

def main():
    args = parse_args()
    spark = SparkSession.builder.appName("dq_check_silver").getOrCreate()

    # Use explicit schema + mergeSchema so the read succeeds even when some
    # partition files are empty (e.g. after a batch run that wrote 0 rows).
    df = (spark.read
          .schema(SILVER_SCHEMA)
          .option("mergeSchema", "true")
          .parquet(f"{args.silver_base}/yellow_tripdata"))
    total             = int(df.count())
    null_trip_distance = int(df.filter(col("trip_distance").isNull()).count())
    null_fare_amount   = int(df.filter(col("fare_amount").isNull()).count())
    bad_distance       = int(df.filter(col("trip_distance") <= 0).count())
    bad_fare           = int(df.filter(col("fare_amount") < 0).count())

    th_null_rate = 0.05
    th_bad_rate  = 0.02

    nr_dist = null_trip_distance / total if total else 1.0
    nr_fare = null_fare_amount   / total if total else 1.0
    br_dist = bad_distance       / total if total else 1.0
    br_fare = bad_fare           / total if total else 1.0

    passed = int((nr_dist <= th_null_rate) and (nr_fare <= th_null_rate)
                 and (br_dist <= th_bad_rate) and (br_fare <= th_bad_rate))

    run_id_val    = str(uuid.uuid4())
    run_epoch_val = int(time.time())

    # Use spark.sql() to build the single-row DataFrame entirely in the JVM.
    # This avoids Python-RDD serialization (cloudpickle) which is broken
    # for PySpark 3.1.x when running on Python 3.11.
    out_df = spark.sql(f"""
        SELECT
            '{run_id_val}'               AS run_id,
            CAST({run_epoch_val}         AS BIGINT)  AS run_epoch,
            CAST({total}                 AS BIGINT)  AS rows_total,
            CAST({null_trip_distance}    AS BIGINT)  AS null_trip_distance,
            CAST({null_fare_amount}      AS BIGINT)  AS null_fare_amount,
            CAST({bad_distance}          AS BIGINT)  AS bad_distance,
            CAST({bad_fare}              AS BIGINT)  AS bad_fare,
            CAST({nr_dist!r}             AS DOUBLE)  AS rate_null_distance,
            CAST({nr_fare!r}             AS DOUBLE)  AS rate_null_fare,
            CAST({br_dist!r}             AS DOUBLE)  AS rate_bad_distance,
            CAST({br_fare!r}             AS DOUBLE)  AS rate_bad_fare,
            CAST({passed}               AS INT)     AS passed
    """)

    (out_df.write
        .format("jdbc")
        .option("url", args.jdbc_url)
        .option("dbtable", "public.dq_results")
        .option("user", args.jdbc_user)
        .option("password", args.jdbc_password)
        .option("driver", "org.postgresql.Driver")
        .mode("append")
        .save())

    print("DQ Results written to public.dq_results")
    spark.stop()

if __name__ == "__main__":
    main()
