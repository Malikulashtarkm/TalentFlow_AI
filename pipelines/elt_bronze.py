import os
import pandas as pd
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from sqlalchemy import create_engine
from prefect import flow, task, get_run_logger

from lake_tables import BRONZE_TABLES
from run_context import latest_blob, make_run_datetime, versioned_blob

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, "config", ".env"))

DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
STORAGE_CONN = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")

if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME, STORAGE_CONN]):
    raise EnvironmentError("Missing required environment variables in config/.env")

PG_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@task
def extract_and_upload(table_name: str, run_datetime: str):
    logger = get_run_logger()
    logger.info(f"Extracting {table_name} from Azure PostgreSQL...")

    engine = create_engine(PG_URL)
    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)

    parquet_buffer = df.to_parquet(index=False)

    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONN)
    file_name = f"{table_name}.parquet"
    for blob_name in [versioned_blob(run_datetime, file_name), latest_blob(file_name)]:
        blob_client = blob_service_client.get_blob_client(
            container="bronze", blob=blob_name
        )
        blob_client.upload_blob(parquet_buffer, overwrite=True)

    logger.info(
        f"{table_name}.parquet uploaded to bronze run {run_datetime} ({len(df)} rows)."
    )


@flow(name="Bronze-Ingestion-Flow")
def bronze_flow(run_datetime: str | None = None):
    run_datetime = run_datetime or make_run_datetime()
    for table in BRONZE_TABLES:
        extract_and_upload(table, run_datetime)
    return run_datetime


if __name__ == "__main__":
    bronze_flow()
