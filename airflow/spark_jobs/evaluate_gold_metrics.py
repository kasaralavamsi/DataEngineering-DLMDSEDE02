
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum, avg as _avg, count as _count
import argparse, uuid, time

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
    df = spark.read.parquet(gold_path)

    months = df.select("year","month").distinct().count()
    rows = df.count()

    totals = df.agg(
        _sum("trips").alias("trips_total"),
        _sum("total_fare").alias("fare_total"),
        _sum("total_tip").alias("tip_total"),
        _avg("avg_distance").alias("avg_distance_over_months")
    ).collect()[0]

    run_id = str(uuid.uuid4())
    run_epoch = int(time.time())

    metrics_data = [(run_id, run_epoch, months, rows, float(totals["trips_total"]), float(totals["fare_total"]), float(totals["tip_total"]), float(totals["avg_distance_over_months"]))]
    cols = ["run_id","run_epoch","months_covered","rows_gold","trips_total","fare_total","tip_total","avg_distance_over_months"]

    out_df = spark.createDataFrame(metrics_data, cols)

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
