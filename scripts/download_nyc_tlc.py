import os, urllib.request
BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"
def download_month(target_dir, year, month, color="yellow"):
    os.makedirs(target_dir, exist_ok=True)
    fn = f"{color}_tripdata_{year}-{month:02d}.parquet"
    url, local = f"{BASE}/{fn}", os.path.join(target_dir, fn)
    if not os.path.exists(local):
        print(f"Downloading {url} -> {local}")
        urllib.request.urlretrieve(url, local)
    return local
