"""
kafka_producer.py
-----------------
Reads a downloaded NYC TLC Parquet file and streams its rows as JSON
messages into a Kafka topic (Bronze-layer ingestion step).

Used by:
    airflow/dags/nyc_taxi_kafka_dag.py  →  download_and_produce task

Kafka topic created/verified : trips_raw   (configurable via `topic` param)
Bootstrap server              : kafka:9092  (internal Docker network address)

Design notes
------------
* Topic pre-creation (_ensure_topic) avoids a race condition where
  kafka-python's first send() triggers broker auto-creation AND waits for
  metadata within max_block_ms — that window is too tight under Docker
  startup load and raises NoBrokersAvailable.

* api_version=(2, 0, 0) is pinned explicitly so the library skips its
  ApiVersionRequest_v0 auto-probe, which times out against the Confluent
  Kafka image used in the Docker Compose stack.

* Datetime columns are normalised to ISO-8601 strings before JSON
  serialisation to avoid "Object of type Timestamp is not JSON serializable"
  errors.

* Rows are flushed every 5 000 records to prevent producer buffer overflow
  when processing large monthly files (≈3 M rows).
"""

import json
import time

import pandas as pd
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _ensure_topic(bootstrap, topic, num_partitions=1, replication_factor=1,
                  retries=5, delay=5):
    """Create the Kafka topic if it does not already exist, with retries.

    Pre-creating the topic avoids the metadata-fetch timeout that occurs when
    kafka-python's first prod.send() triggers auto-topic-creation: the broker
    must create the topic *and* return metadata within max_block_ms, which
    frequently fails under load.  Doing it here with explicit retries gives
    the broker time to finish initialisation before we start sending rows.

    Parameters
    ----------
    bootstrap : str
        Kafka bootstrap server, e.g. 'kafka:9092'.
    topic : str
        Name of the topic to create.
    num_partitions : int
        Number of partitions for the new topic (default 1).
    replication_factor : int
        Replication factor (default 1 — suitable for a single-node cluster).
    retries : int
        Maximum number of creation attempts before raising RuntimeError.
    delay : int
        Base wait time in seconds between attempts (increases linearly).
    """
    for attempt in range(1, retries + 1):
        try:
            # Open a short-lived admin client just for topic management.
            admin = KafkaAdminClient(
                bootstrap_servers=bootstrap,
                api_version=(2, 0, 0),        # skip auto-probe (see module docstring)
                request_timeout_ms=30000,      # 30 s — generous for Docker startup
            )
            try:
                admin.create_topics([
                    NewTopic(name=topic,
                             num_partitions=num_partitions,
                             replication_factor=replication_factor)
                ])
                print(f"Topic '{topic}' created.")
            except TopicAlreadyExistsError:
                # Idempotent — topic already exists, nothing to do.
                print(f"Topic '{topic}' already exists — skipping creation.")
            finally:
                admin.close()   # always release the admin connection
            return  # success — exit retry loop

        except Exception as exc:
            print(f"[attempt {attempt}/{retries}] Topic-ensure failed: {exc}")
            if attempt < retries:
                # Exponential-ish back-off: 5 s, 10 s, 15 s, 20 s …
                time.sleep(delay * attempt)

    # All retries exhausted — raise so the Airflow task is marked failed.
    raise RuntimeError(
        f"Could not ensure topic '{topic}' after {retries} attempts"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def produce_parquet_to_kafka(
    parquet_path, bootstrap="kafka:9092", topic="trips_raw", limit=50000
):
    """Read a Parquet file and publish its rows as JSON to a Kafka topic.

    Each row is serialised as a UTF-8 encoded JSON object and sent to
    `topic` using the default round-robin partitioner.

    Parameters
    ----------
    parquet_path : str
        Path to the local Parquet file (output of download_month()).
    bootstrap : str, optional
        Kafka bootstrap server address (default 'kafka:9092').
    topic : str, optional
        Destination Kafka topic name (default 'trips_raw').
    limit : int or None, optional
        Cap on the number of rows sent per call.  Useful for development /
        cost control.  Set to None to send the full file (default 50 000).

    Returns
    -------
    bool
        True when all rows have been produced and the producer flushed.
    """
    # ------------------------------------------------------------------ #
    # 1. Load and optionally cap the dataset                               #
    # ------------------------------------------------------------------ #
    df = pd.read_parquet(parquet_path)

    if limit:
        # Slice to the first `limit` rows to keep dev runs fast.
        df = df.head(limit)

    # ------------------------------------------------------------------ #
    # 2. Normalise datetime columns → ISO-8601 strings                    #
    # ------------------------------------------------------------------ #
    # pandas Timestamps are not JSON-serialisable by default.
    # Converting to strings here avoids a TypeError at serialisation time.
    for col in df.columns:
        if "datetime" in col or "timestamp" in col:
            df[col] = (
                pd.to_datetime(df[col], errors="coerce")
                  .dt.strftime("%Y-%m-%dT%H:%M:%S")   # ISO-8601, no timezone
            )

    # ------------------------------------------------------------------ #
    # 3. Ensure the target topic exists before producing                  #
    # ------------------------------------------------------------------ #
    # See _ensure_topic docstring for why we pre-create rather than relying
    # on broker auto-creation.
    _ensure_topic(bootstrap, topic)

    # ------------------------------------------------------------------ #
    # 4. Create the Kafka producer                                         #
    # ------------------------------------------------------------------ #
    # Pin api_version explicitly so kafka-python skips the broker-version
    # auto-probe (ApiVersionRequest_v0).  Without this, the library times
    # out (~2 s) probing the Confluent/Apache Kafka broker and raises
    # NoBrokersAvailable even when the broker is healthy.
    # (2, 0, 0) covers all features used here and is compatible with
    # Kafka 2.x / 3.x brokers shipped in the Docker Compose stack.
    prod = KafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        api_version=(2, 0, 0),
        request_timeout_ms=60000,       # 60 s per request
        max_block_ms=180000,            # 3-min ceiling: metadata fetch + backpressure
        connections_max_idle_ms=300000, # keep connection alive for long files
    )

    # ------------------------------------------------------------------ #
    # 5. Stream rows to Kafka                                              #
    # ------------------------------------------------------------------ #
    sent = 0
    for _, row in df.iterrows():
        prod.send(topic, row.to_dict())   # async send — buffered internally
        sent += 1

        if sent % 5000 == 0:
            # Periodic flush: drains the internal send buffer to prevent
            # memory / timeout issues on large files (>1 M rows).
            prod.flush()
            print(f"  ...{sent} rows sent to '{topic}'")

    # Final flush + clean shutdown — ensures all buffered messages are
    # delivered before the Airflow task marks itself complete.
    prod.flush()
    prod.close()
    print(f"Produced {sent} rows to topic '{topic}'")
    return True
