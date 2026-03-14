"""
download_nyc_tlc.py
-------------------
Utility for downloading NYC TLC (Taxi & Limousine Commission) trip-data
Parquet files from the official TLC CloudFront CDN.

Used by:
    airflow/dags/nyc_taxi_kafka_dag.py  →  download_and_produce task
    airflow/dags/nyc_taxi_batch_dag.py  →  download_raw task

The downloaded file is the Bronze-layer input for the Medallion pipeline.
Files are cached locally; if the file already exists on disk it is NOT
re-downloaded (idempotent).

CDN base URL pattern:
    https://d37ci6vzurychx.cloudfront.net/trip-data/{color}_tripdata_{YYYY}-{MM}.parquet
"""

import os
import urllib.request

# Official TLC data CDN — serves Parquet files from 2022 onward.
BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"


def download_month(target_dir, year, month, color="yellow"):
    """Download a single month of TLC trip data as a Parquet file.

    Parameters
    ----------
    target_dir : str
        Local directory where the Parquet file will be saved.
        Created automatically if it does not exist.
    year : int
        4-digit year, e.g. 2024.
    month : int
        Month number (1–12).
    color : str, optional
        Taxi colour category: 'yellow' (default), 'green', or 'fhv'.

    Returns
    -------
    str
        Absolute path to the downloaded (or already-cached) Parquet file.

    Example
    -------
    >>> path = download_month("/tmp/raw", 2024, 1)
    >>> # /tmp/raw/yellow_tripdata_2024-01.parquet
    """
    # Ensure the destination directory exists (mkdir -p equivalent).
    os.makedirs(target_dir, exist_ok=True)

    # Build the remote filename and URL following the TLC naming convention.
    fn = f"{color}_tripdata_{year}-{month:02d}.parquet"   # zero-pad month
    url = f"{BASE}/{fn}"
    local = os.path.join(target_dir, fn)

    if not os.path.exists(local):
        # File not cached — download from CDN.
        print(f"Downloading {url} -> {local}")
        urllib.request.urlretrieve(url, local)
    else:
        # File already present — skip download to save time and bandwidth.
        print(f"Already cached: {local}")

    return local
