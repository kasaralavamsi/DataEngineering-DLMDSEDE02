
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import argparse, time, uuid

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

    df = spark.read.parquet(f"{args.silver_base}/yellow_tripdata")
    total = df.count()
    null_trip_distance = df.filter(col("trip_distance").isNull()).count()
    null_fare_amount = df.filter(col("fare_amount").isNull()).count()
    bad_distance = df.filter(col("trip_distance") <= 0).count()
    bad_fare = df.filter(col("fare_amount") < 0).count()

    th_null_rate = 0.05
    th_bad_rate = 0.02

    nr_dist = null_trip_distance / total if total else 1.0
    nr_fare = null_fare_amount / total if total else 1.0
    br_dist = bad_distance / total if total else 1.0
    br_fare = bad_fare / total if total else 1.0

    passed = int((nr_dist <= th_null_rate) and (nr_fare <= th_null_rate) and (br_dist <= th_bad_rate) and (br_fare <= th_bad_rate))

    data = [(str(uuid.uuid4()), int(time.time()), total, null_trip_distance, null_fare_amount, bad_distance, bad_fare, nr_dist, nr_fare, br_dist, br_fare, passed)]
    cols = ["run_id","run_epoch","rows_total","null_trip_distance","null_fare_amount","bad_distance","bad_fare","rate_null_distance","rate_null_fare","rate_bad_distance","rate_bad_fare","passed"]
    out_df = spark.createDataFrame(data, cols)

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
