
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, year, month
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
import argparse

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", default="kafka:9092")
    p.add_argument("--topic", default="trips_raw")
    p.add_argument("--bronze_base", required=True)
    p.add_argument("--startingOffsets", default="earliest")
    p.add_argument("--endingOffsets", default="latest")
    return p.parse_args()

schema = StructType([
    StructField("tpep_pickup_datetime", StringType()),
    StructField("tpep_dropoff_datetime", StringType()),
    StructField("passenger_count", DoubleType()),
    StructField("trip_distance", DoubleType()),
    StructField("fare_amount", DoubleType()),
    StructField("tip_amount", DoubleType()),
    StructField("PULocationID", IntegerType()),
    StructField("DOLocationID", IntegerType()),
    StructField("payment_type", IntegerType()),
])

def main():
    args = parse_args()
    spark = SparkSession.builder.appName("spark_kafka_to_bronze_batch").getOrCreate()

    df_raw = (spark.read
        .format("kafka")
        .option("kafka.bootstrap.servers", args.bootstrap)
        .option("subscribe", args.topic)
        .option("startingOffsets", args.startingOffsets)
        .option("endingOffsets", args.endingOffsets)
        .load())

    df_val = df_raw.selectExpr("CAST(value AS STRING) AS json_str")
    df = df_val.select(from_json(col("json_str"), schema).alias("r")).select("r.*")

    df2 = (df
        .withColumn("pickup_ts", to_timestamp(col("tpep_pickup_datetime")))
        .withColumn("year", year(col("pickup_ts")))
        .withColumn("month", month(col("pickup_ts"))))

    out = f"{args.bronze_base}/yellow_tripdata"
    (df2.repartition("year","month")
        .write.mode("append")
        .partitionBy("year","month")
        .parquet(out))

    print("Wrote Kafka batch to Bronze:", out)
    spark.stop()

if __name__ == "__main__":
    main()
