
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, year, month, lit
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

def main():
    args = parse_args()
    spark = SparkSession.builder.appName("nyc_bronze_to_silver").getOrCreate()

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
        df = spark.read.option("basePath", src).parquet(src)
        df2 = (df
            .filter(col("trip_distance") > 0)
            .filter(col("fare_amount") >= 0)
            .withColumn("pickup_date", to_date(col("tpep_pickup_datetime")))
            .withColumn("year", year(col("pickup_date")))
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
