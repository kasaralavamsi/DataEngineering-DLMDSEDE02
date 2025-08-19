from pyspark.sql import SparkSession

POSTGRES_URL = "jdbc:postgresql://postgres:5432/nyc"
POSTGRES_PROPS = {"user": "nyc", "password": "nyc", "driver": "org.postgresql.Driver"}

def main():
    spark = (
        SparkSession.builder
        .appName("load_taxi_zone_lookup")
        .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0")
        # If packages download is blocked, mount the jar and use:
        # .config("spark.jars", "/opt/spark/jars/postgresql-42.6.0.jar")
        .getOrCreate()
    )

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv("hdfs://namenode:9000/datasets/taxi_zone_lookup.csv")
    )

    df.show(5, truncate=False)

    (df.write.mode("overwrite")
        .jdbc(POSTGRES_URL, "public.taxi_zone_lookup", properties=POSTGRES_PROPS))

    spark.stop()

if __name__ == "__main__":
    main()
