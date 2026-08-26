import os
import sys
import pandas as pd
import tempfile
import hashlib
import uuid
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from prefect import flow, task, get_run_logger

from lake_tables import PII_TABLES, PASS_THROUGH_TABLES
from run_context import latest_blob, make_run_datetime, versioned_blob

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "utils"))

from crypto_utils import odin_encrypt

load_dotenv(os.path.join(project_root, "config", ".env"))

STORAGE_CONN = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
if not STORAGE_CONN:
    raise EnvironmentError("AZURE_STORAGE_CONNECTION_STRING is missing from config/.env")


def _temp_parquet_path() -> str:
    """Return a closed temp file path (Windows-safe — no open handle)."""
    fd, path = tempfile.mkstemp(suffix=".parquet")
    os.close(fd)
    return path


def _get_blob_client(container: str, blob_name: str):
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONN)
    return blob_service_client.get_blob_client(container=container, blob=blob_name)


def _download_existing_silver(blob_name: str):
    path = _temp_parquet_path()
    try:
        blob_client = _get_blob_client("silver", latest_blob(blob_name))
        with open(path, "wb") as f:
            f.write(blob_client.download_blob().readall())
        return path
    except ResourceNotFoundError:
        _safe_remove(path)
        return None


def _upload_to_silver(file_path: str, blob_name: str, run_datetime: str):
    for target_blob in [versioned_blob(run_datetime, blob_name), latest_blob(blob_name)]:
        blob_client = _get_blob_client("silver", target_blob)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)


def _safe_remove(file_path: str):
    if file_path and os.path.exists(file_path):
        os.remove(file_path)


def _row_hash(row, columns):
    values = ["" if pd.isna(row[col]) else str(row[col]) for col in columns]
    return hashlib.sha256("||".join(values).encode("utf-8")).hexdigest()


def _business_key_string(value) -> str:
    """Normalize UUID values that may come back from parquet as bytes."""
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, bytes):
        if len(value) == 16:
            return str(uuid.UUID(bytes=value))
        return value.hex()
    return str(value)


def _apply_scd2_snapshot(df: pd.DataFrame, existing_path: str | None) -> pd.DataFrame:
    business_key = "candidate_id"
    ignored_columns = {"start_date", "end_date", "is_current", "row_hash"}
    tracked_columns = [
        col for col in df.columns if col not in ignored_columns and col != business_key
    ]
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    df = df.copy()
    if business_key in df.columns:
        df[business_key] = df[business_key].map(_business_key_string)
    df["row_hash"] = df.apply(lambda row: _row_hash(row, tracked_columns), axis=1)
    df["start_date"] = now
    df["end_date"] = pd.NaT
    df["is_current"] = True
    df["_needs_encryption"] = True

    if not existing_path:
        return df

    existing = pd.read_parquet(existing_path)
    if existing.empty or "row_hash" not in existing.columns:
        return df
    if business_key in existing.columns:
        existing[business_key] = existing[business_key].map(_business_key_string)

    current_existing = existing[existing["is_current"] == True].copy()
    current_hashes = dict(
        zip(current_existing[business_key].map(_business_key_string), current_existing["row_hash"])
    )

    changed_keys = set()
    new_rows = []
    for _, row in df.iterrows():
        key = _business_key_string(row[business_key])
        if current_hashes.get(key) != row["row_hash"]:
            changed_keys.add(key)
            new_rows.append(row)

    if changed_keys:
        mask = existing[business_key].map(_business_key_string).isin(changed_keys) & (existing["is_current"] == True)
        existing.loc[mask, "is_current"] = False
        existing.loc[mask, "end_date"] = now

    if not new_rows:
        existing["_needs_encryption"] = False
        return existing

    return pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)


@task
def download_bronze_parquet(table_name: str, run_datetime: str) -> str:
    path = _temp_parquet_path()
    blob_client = _get_blob_client(
        "bronze",
        versioned_blob(run_datetime, f"{table_name}.parquet"),
    )
    with open(path, "wb") as f:
        f.write(blob_client.download_blob().readall())
    return path


@task
def process_pii_table(table_name: str, config: dict, run_datetime: str):
    logger = get_run_logger()
    logger.info(f"Encrypting PII for {table_name}...")

    bronze_path = download_bronze_parquet(table_name, run_datetime)
    silver_path = _temp_parquet_path()

    try:
        df = pd.read_parquet(bronze_path)

        if config.get("scd2"):
            existing_path = _download_existing_silver(config["silver_blob"])
            try:
                df = _apply_scd2_snapshot(df, existing_path)
            finally:
                _safe_remove(existing_path)

        for col in config["columns"]:
            if col in df.columns:
                # Some PII columns arrive as numbers, but encrypted values are text.
                df[col] = df[col].astype("object")
                if "_needs_encryption" in df.columns:
                    mask = df["_needs_encryption"].fillna(False)
                    df.loc[mask, col] = df.loc[mask, col].apply(odin_encrypt)
                else:
                    df[col] = df[col].apply(odin_encrypt)

        if "_needs_encryption" in df.columns:
            df = df.drop(columns=["_needs_encryption"])

        df.to_parquet(silver_path, index=False)
        _upload_to_silver(silver_path, config["silver_blob"], run_datetime)
        logger.info(f"{config['silver_blob']} uploaded to silver run {run_datetime}.")
    finally:
        _safe_remove(bronze_path)
        _safe_remove(silver_path)


@task
def copy_bronze_to_silver(table_name: str, run_datetime: str):
    logger = get_run_logger()
    logger.info(f"Copying {table_name} bronze -> silver...")

    bronze_path = download_bronze_parquet(table_name, run_datetime)
    try:
        _upload_to_silver(bronze_path, f"{table_name}.parquet", run_datetime)
        logger.info(f"{table_name}.parquet copied to silver run {run_datetime}.")
    finally:
        _safe_remove(bronze_path)


@flow(name="Silver-Secure-Flow")
def silver_flow(run_datetime: str | None = None):
    run_datetime = run_datetime or make_run_datetime()
    logger = get_run_logger()
    logger.info(f"Starting silver transformation for run {run_datetime}...")

    for table_name, config in PII_TABLES.items():
        process_pii_table(table_name, config, run_datetime)

    for table_name in PASS_THROUGH_TABLES:
        copy_bronze_to_silver(table_name, run_datetime)

    logger.info("Silver layer transformation complete.")
    return run_datetime


if __name__ == "__main__":
    silver_flow()
