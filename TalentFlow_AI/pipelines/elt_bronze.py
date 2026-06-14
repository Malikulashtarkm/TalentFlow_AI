import os
import pandas as pd
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from sqlalchemy import create_engine
from prefect import flow, task, get_run_logger

# Load secrets
load_dotenv("config/.env")

# --- AZURE CONFIG ---
PG_URL = f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASS')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
# Replace with your actual connection string or add it to .env
STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")

# =============================================================================
# PREFECT TASKS (The "Muscle")
# =============================================================================

@task(retries=3, retry_delay_seconds=10)
def extract_table_to_df(table_name):
    """Task to extract data from Postgres to a DataFrame."""
    logger = get_run_logger()
    logger.info(f"📦 Extracting {table_name} from Azure Postgres...")
    
    engine = create_engine(PG_URL)
    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    
    logger.info(f"✅ Extracted {len(df)} rows from {table_name}.")
    return df

@task
def upload_parquet_to_lake(table_name, df):
    """Task to save DataFrame as Parquet in ADLS Gen2 Bronze layer."""
    logger = get_run_logger()
    
    # Convert to Parquet in memory
    parquet_buffer = df.to_parquet(index=False)
    
    # Upload to Azure
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container="bronze", blob=f"{table_name}.parquet")
    blob_client.upload_blob(parquet_buffer, overwrite=True)
    
    logger.info(f"☁️ {table_name}.parquet successfully uploaded to Bronze Lake.")

# =============================================================================
# PREFECT FLOW (The "Brain")
# =============================================================================

@flow(name="Bronze-Ingestion-Pipeline")
def bronze_ingestion_flow():
    """The main flow that orchestrates the extraction and loading process."""
    logger = get_run_logger()
    logger.info("🚀 Starting Bronze Ingestion Flow...")
    
    # Tables we want to move to the warehouse
    tables = ["candidates", "candidate_education", "login_logs", "interview_feedback", "interview_schedules"]
    
    for table in tables:
        # Task 1: Extract
        df = extract_table_to_df(table)
        # Task 2: Load
        upload_parquet_to_lake(table, df)
        
    logger.info("🏁 Bronze Ingestion Complete!")

if __name__ == "__main__":
    # Run the flow locally to test it
    bronze_ingestion_flow()