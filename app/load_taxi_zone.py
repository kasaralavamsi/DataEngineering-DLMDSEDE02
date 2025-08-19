from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("load_taxi_zone_lookup")
         .getOrCreate())

df = (spark.read
      .option("header","true")
      .csv("hdfs://namenode:9000/datasets/taxi_zone_lookup.csv"))

(df.write
   .format("jdbc")
   .option("url","jdbc:postgresql://postgres:5432/nyc")
   .option("dbtable","public.taxi_zone_lookup")
   .option("user","nyc")
   .option("password","nyc")
   .option("driver","org.postgresql.Driver")
   .mode("overwrite")
   .save())
spark.stop()
