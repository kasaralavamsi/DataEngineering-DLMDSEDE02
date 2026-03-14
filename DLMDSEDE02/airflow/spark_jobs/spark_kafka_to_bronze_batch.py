
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, year, month
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
import argparse

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", default="kafka:9092")
    p.add_argument("--topic", default="trips_raw")
    p.add_argument("--bronze_base", required=True)
    p.add_argument("--startingOffsets", default="earliest")
    p.add_argument("--endingOffsets", default="latest")
    p.add_argument("--num_partitions", type=int, default=1,
                   help="Number of Kafka topic partitions (default 1 for "
                        "auto-created topics in a single-broker cluster)")
    return p.parse_args()

# JSON schema for Kafka messages.  Datetime fields are parsed as String first
# (Kafka delivers them as JSON text), then cast to TimestampType below so that
# bronze Parquet files are physically compatible with download-pipeline files.
# All numeric ID columns use DoubleType to match the download-pipeline schema;
# IntegerType (INT32) would cause MutableDouble/MutableLong cast errors when
# the silver job reads a mixed bronze directory.
KAFKA_SCHEMA = StructType([
    StructField("tpep_pickup_datetime",  StringType(),  True),
    StructField("tpep_dropoff_datetime", StringType(),  True),
    StructField("passenger_count",       DoubleType(),  True),
    StructField("trip_distance",         DoubleType(),  True),
    StructField("fare_amount",           DoubleType(),  True),
    StructField("tip_amount",            DoubleType(),  True),
    StructField("PULocationID",          DoubleType(),  True),
    StructField("DOLocationID",          DoubleType(),  True),
    StructField("payment_type",          DoubleType(),  True),
])

def main():
    args = parse_args()
    spark = (SparkSession.builder
        .appName("spark_kafka_to_bronze_batch")
        # Dynamic partition overwrite: only the partitions present in the
        # DataFrame are replaced, leaving other year/month partitions intact.
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate())

    # -----------------------------------------------------------------------
    # Use "assign" mode instead of "subscribe" when reading Kafka in batch.
    #
    # "subscribe" requires consumer-group coordination via the
    # __consumer_offsets internal topic.  In single-broker Docker setups the
    # group-coordinator election can fail indefinitely, producing an endless
    # stream of NotCoordinatorException warnings until the driver is OOM-killed.
    #
    # "assign" bypasses the group coordinator entirely: Spark is given explicit
    # partition assignments and reads directly from the broker, which is safe
    # and correct for batch (non-streaming) Kafka reads.
    # -----------------------------------------------------------------------
    assign_spec = json.dumps(
        {args.topic: list(range(args.num_partitions))}
    )

    df_raw = (spark.read
        .format("kafka")
        .option("kafka.bootstrap.servers", args.bootstrap)
        # Explicit partition assignment – no consumer-group coordinator needed.
        .option("assign", assign_spec)
        .option("startingOffsets", args.startingOffsets)
        .option("endingOffsets", args.endingOffsets)
        # Tolerate gaps caused by log compaction / retention without aborting.
        .option("failOnDataLoss", "false")
        # -----------------------------------------------------------------------
        # Consumer timeout / backoff settings.
        #
        # Even in "assign" mode the Kafka client still initialises an internal
        # coordinator connection.  Without these settings the client retries at
        # full speed and floods the logs with
        # "Group coordinator … is unavailable or invalid, will attempt rediscovery"
        # during the brief window while the broker is still electing a leader for
        # __consumer_offsets.  These values tell the client to wait and back off
        # rather than spin.
        # -----------------------------------------------------------------------
        .option("kafka.request.timeout.ms", "60000")
        .option("kafka.session.timeout.ms", "30000")
        .option("kafka.heartbeat.interval.ms", "10000")
        .option("kafka.metadata.max.age.ms", "300000")
        .option("kafka.reconnect.backoff.ms", "1000")
        .option("kafka.reconnect.backoff.max.ms", "10000")
        .option("kafka.retry.backoff.ms", "3000")
        .load())

    df_val = df_raw.selectExpr("CAST(value AS STRING) AS json_str")
    df = df_val.select(from_json(col("json_str"), KAFKA_SCHEMA).alias("r")).select("r.*")

    # Cast string datetimes → TimestampType so bronze Parquet files are
    # physically compatible with download-pipeline files (both use INT96).
    df2 = (df
        .withColumn("tpep_pickup_datetime",
                    to_timestamp(col("tpep_pickup_datetime")))
        .withColumn("tpep_dropoff_datetime",
                    to_timestamp(col("tpep_dropoff_datetime")))
        .withColumn("year",  year(col("tpep_pickup_datetime")))
        .withColumn("month", month(col("tpep_pickup_datetime"))))

    out = f"{args.bronze_base}/yellow_tripdata"
    (df2.repartition("year", "month")
        .write.mode("overwrite")        # dynamic overwrite – only touches affected partitions
        .partitionBy("year", "month")
        .parquet(out))

    print("Wrote Kafka batch to Bronze:", out)
    spark.stop()

if __name__ == "__main__":
    main()
