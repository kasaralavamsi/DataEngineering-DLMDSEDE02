# -*- coding: utf-8 -*-
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, length, current_timestamp

INPUT_HDFS = os.getenv("INPUT_HDFS", "hdfs://namenode:9000/data/raw/taxi_zone_lookup.csv")
PG_URL     = os.getenv("PG_URL", "jdbc:postgresql://postgres:5432/nyc")
PG_USER    = os.getenv("PG_USER", "nyc")
PG_PASS    = os.getenv("PG_PASS", "nyc")
PG_TABLE   = os.getenv("PG_TABLE", "public.batch_clean")

def main():
    spark = (
        SparkSession.builder
        .appName("Phase3BatchJob")
        .getOrCreate()
    )

    # Read CSV from HDFS
    df_raw = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(INPUT_HDFS)
    )

    # Basic cleaning
    df = (
        df_raw
        .withColumn("LocationID", col("LocationID").cast("int"))
        .withColumn("Borough", trim(col("Borough")))
        .withColumn("Zone", trim(col("Zone")))
        .withColumn("service_zone", trim(col("service_zone")))
        .filter(
            (length(col("Borough")) > 0) |
            (length(col("Zone")) > 0) |
            (length(col("service_zone")) > 0) |
            col("LocationID").isNotNull()
        )
        .withColumn("loaded_at", current_timestamp())
    )

    # Write to Postgres
    (
        df.write
        .format("jdbc")
        .option("url", PG_URL)
        .option("dbtable", PG_TABLE)
        .option("user", PG_USER)
        .option("password", PG_PASS)
        .option("driver", "org.postgresql.Driver")
        .mode("overwrite")
        .save()
    )

    print("✅ Wrote DataFrame to Postgres table", PG_TABLE)
    spark.stop()

if __name__ == "__main__":
    main()