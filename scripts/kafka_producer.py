import json, pandas as pd
from kafka import KafkaProducer
def produce_parquet_to_kafka(parquet_path, bootstrap="kafka:9092", topic="trips_raw", limit=50000):
    df = pd.read_parquet(parquet_path)
    if limit: df = df.head(limit)
    for col in df.columns:
        if "datetime" in col or "timestamp" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S")
    prod = KafkaProducer(bootstrap_servers=bootstrap, value_serializer=lambda v: json.dumps(v).encode("utf-8"))
    for _, row in df.iterrows(): prod.send(topic, row.to_dict())
    prod.flush(); return True
