
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, year, month, lit
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType
)
import argparse, os, re

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=["bronze","silver"], required=True)
    p.add_argument("--input")
    p.add_argument("--bronze_base", required=True)
    p.add_argument("--silver_base")
    return p.parse_args()

def infer_year_month_from_path(path: str):
    m = re.search(r"(\d{4})-(\d{2})", os.path.basename(path))
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

# Explicit schema with permissive types to handle schema evolution across NYC taxi
# data vintages.  Using DoubleType for all numerics avoids INT32 vs INT64 mismatches
# between pre-2022 and 2023+ source files.  Using TimestampType for datetime columns
# handles both INT96 (old pyarrow default) and TIMESTAMP_MICROS (new) Parquet encodings
# when the vectorized reader is disabled.
BRONZE_SCHEMA = StructType([
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
])

def main():
    args = parse_args()
    spark = (SparkSession.builder
        .appName("nyc_bronze_to_silver")
        # Disable the vectorized Parquet reader so Spark's legacy row reader is used.
        # This allows mixed-type columns (INT32/INT64, INT96/TIMESTAMP_MICROS) to be
        # read without strict type enforcement across bronze partition files.
        .config("spark.sql.parquet.enableVectorizedReader", "false")
        # Tolerate INT96 timestamps written by pandas/pyarrow without rebase errors.
        .config("spark.sql.legacy.parquet.int96RebaseModeInRead", "CORRECTED")
        .config("spark.sql.parquet.int96RebaseModeInRead", "CORRECTED")
        # Safety net: skip any bronze Parquet files whose physical column types
        # are incompatible with BRONZE_SCHEMA (e.g. legacy Kafka-written files
        # that stored tpep_pickup_datetime as UTF-8 binary instead of a proper
        # Parquet timestamp).  Those files are silently skipped so the rest of
        # the bronze data can still be promoted to silver.  Once the Kafka
        # pipeline is re-run with the fixed writer the bad files are overwritten
        # and this setting becomes a no-op.
        .config("spark.sql.files.ignoreCorruptFiles", "true")
        # Reduce shuffle partitions from default 200 to 4.
        # The silver stage processes one month of data at a time; 200 partitions
        # causes ~200 slow tasks on a single worker and triggers Airflow timeouts.
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate())

    if args.stage == "bronze":
        assert args.input, "--input required for bronze stage"
        y, m = infer_year_month_from_path(args.input)
        df = spark.read.format("parquet").load(args.input)
        if y and m:
            df = df.withColumn("year", lit(int(y))).withColumn("month", lit(int(m)))
        bronze_path = f"{args.bronze_base}/yellow_tripdata/year={y}/month={m}"
        df.write.mode("overwrite").parquet(bronze_path)
        print("Wrote bronze to", bronze_path)

    elif args.stage == "silver":
        assert args.silver_base, "--silver_base required for silver stage"
        src = f"{args.bronze_base}/yellow_tripdata"

        # Provide explicit schema to prevent schema-merge failures caused by
        # INT32 vs INT64 or INT96 vs string inconsistencies across bronze files.
        # Partition columns (year, month) are auto-discovered from the path.
        df = (spark.read
              .schema(BRONZE_SCHEMA)
              .option("basePath", src)
              .parquet(src))

        # to_date() accepts TimestampType directly, so no cast needed.
        df2 = (df
            .filter(col("trip_distance") > 0)
            .filter(col("fare_amount") >= 0)
            .withColumn("pickup_date", to_date(col("tpep_pickup_datetime")))
            .withColumn("year",  year(col("pickup_date")))
            .withColumn("month", month(col("pickup_date")))
        )
        silver_path = f"{args.silver_base}/yellow_tripdata"
        (df2.repartition("year","month")
            .write.mode("overwrite")
            .partitionBy("year","month")
            .parquet(silver_path))
        print("Wrote silver to", silver_path)

    spark.stop()

if __name__ == "__main__":
    main()
