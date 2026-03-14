import json, time, pandas as pd
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError


def _ensure_topic(bootstrap, topic, num_partitions=1, replication_factor=1,
                  retries=5, delay=5):
    """Create the Kafka topic if it does not already exist, with retries.

    Pre-creating the topic avoids the metadata-fetch timeout that occurs when
    kafka-python's first prod.send() triggers auto-topic-creation: the broker
    must create the topic *and* return metadata within max_block_ms, which
    frequently fails under load.  Doing it here with explicit retries gives
    the broker time to finish initialization before we start sending rows.
    """
    for attempt in range(1, retries + 1):
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=bootstrap,
                api_version=(2, 0, 0),
                request_timeout_ms=30000,
            )
            try:
                admin.create_topics([
                    NewTopic(name=topic,
                             num_partitions=num_partitions,
                             replication_factor=replication_factor)
                ])
                print(f"Topic '{topic}' created.")
            except TopicAlreadyExistsError:
                print(f"Topic '{topic}' already exists — skipping creation.")
            finally:
                admin.close()
            return  # success
        except Exception as exc:
            print(f"[attempt {attempt}/{retries}] Topic-ensure failed: {exc}")
            if attempt < retries:
                time.sleep(delay * attempt)
    raise RuntimeError(
        f"Could not ensure topic '{topic}' after {retries} attempts"
    )


def produce_parquet_to_kafka(
    parquet_path, bootstrap="kafka:9092", topic="trips_raw", limit=50000
):
    df = pd.read_parquet(parquet_path)
    if limit:
        df = df.head(limit)

    # Serialise datetime columns as ISO strings so the JSON payload is clean.
    for col in df.columns:
        if "datetime" in col or "timestamp" in col:
            df[col] = (
                pd.to_datetime(df[col], errors="coerce")
                .dt.strftime("%Y-%m-%dT%H:%M:%S")
            )

    # Pre-create the topic before producing — avoids metadata-fetch timeout
    # on the first send() when the topic is being auto-created by the broker.
    _ensure_topic(bootstrap, topic)

    # Pin api_version explicitly so kafka-python skips the broker-version
    # auto-probe (ApiVersionRequest_v0).  Without this the library times out
    # after ~2 s probing the Confluent/Apache Kafka broker and raises
    # NoBrokersAvailable even though the broker is healthy.
    # (2, 0, 0) covers all features used here and is compatible with
    # Kafka 2.x/3.x brokers shipped in the Docker Compose stack.
    prod = KafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        api_version=(2, 0, 0),
        request_timeout_ms=60000,
        max_block_ms=180000,       # 3-min ceiling for metadata + send backpressure
        connections_max_idle_ms=300000,
    )

    sent = 0
    for _, row in df.iterrows():
        prod.send(topic, row.to_dict())
        sent += 1
        if sent % 5000 == 0:
            prod.flush()           # periodic flush to avoid buffer overflow
            print(f"  ...{sent} rows sent to '{topic}'")

    prod.flush()
    prod.close()
    print(f"Produced {sent} rows to topic '{topic}'")
    return True
