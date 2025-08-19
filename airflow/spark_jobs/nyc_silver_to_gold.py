
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum, avg as _avg, count as _count, round as _round
import argparse

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
    spark = SparkSession.builder.appName("nyc_silver_to_gold").getOrCreate()

    silver_path = f"{args.silver_base}/yellow_tripdata"
    df = spark.read.option("basePath", silver_path).parquet(silver_path)

    kpis = (df.groupBy("year","month")
              .agg(
                   _count("*").alias("trips"),
                   _round(_sum("fare_amount"),2).alias("total_fare"),
                   _round(_sum("tip_amount"),2).alias("total_tip"),
                   _round(_avg("trip_distance"),2).alias("avg_distance")
              ))

    gold_path = f"{args.gold_base}/kpis_trips_monthly"
    (kpis.repartition("year","month")
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
