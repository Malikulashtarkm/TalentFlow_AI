import os
import pandas as pd
import duckdb
import tempfile
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from prefect import flow, task, get_run_logger

load_dotenv("config/.env")

# --- AZURE CONFIG ---
STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")

@task
def download_parquet_to_temp(container, filename):
    """Downloads a parquet file from Azure and saves it as a temporary local file."""
    logger = get_run_logger()
    logger.info(f"📥 Downloading {filename} from {container}...")
    
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=container, blob=filename)
    
    # Create a temporary file that persists until we close it
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    with open(temp_file.name, "wb") as f:
        f.write(blob_client.download_blob().readall())
    
    return temp_file.name

@task
def apply_scd_type2_logic(bronze_path, silver_path=None):
    """Implements SCD Type 2 logic using DuckDB on local parquet files."""
    logger = get_run_logger()
    logger.info("⚙️ Applying SCD Type 2 Versioning via DuckDB...")

    con = duckdb.connect(database=':memory:')

    # 1. Load Bronze data using the FILE PATH
    con.execute(f"CREATE TABLE bronze_candidates AS SELECT * FROM read_parquet('{bronze_path}')")

    if silver_path:
        # Load existing Silver data using the FILE PATH
        con.execute(f"CREATE TABLE silver_candidates AS SELECT * FROM read_parquet('{silver_path}')")
        
        # --- SCD TYPE 2 LOGIC ---
        con.execute("""
            UPDATE silver_candidates
            SET is_current = False, end_date = CURRENT_TIMESTAMP
            WHERE candidate_id IN (
                SELECT b.candidate_id FROM bronze_candidates b
                JOIN silver_candidates s ON b.candidate_id = s.candidate_id
                WHERE s.is_current = True 
                AND (b.city != s.city OR b.state != s.state OR b.expected_salary != s.expected_salary)
            )
        """)

        con.execute("""
            INSERT INTO silver_candidates 
            SELECT 
                (random() * 1000000)::INT as candidate_sk, 
                b.candidate_id, b.email, b.first_name, b.last_name, 
                b.city, b.state, b.degree, b.expected_salary, 
                CURRENT_TIMESTAMP as start_date, NULL as end_date, True as is_current
            FROM bronze_candidates b
            LEFT JOIN silver_candidates s ON b.candidate_id = s.candidate_id AND s.is_current = True
            WHERE s.candidate_id IS NULL 
               OR (b.city != s.city OR b.state != s.state OR b.expected_salary != s.expected_salary)
        """)
    else:
        # Initial Load
        con.execute("""
            CREATE TABLE silver_candidates AS 
            SELECT 
                (random() * 1000000)::INT as candidate_sk,
                candidate_id, email, first_name, last_name, 
                city, state, degree, expected_salary, 
                CURRENT_TIMESTAMP as start_date, NULL as end_date, True as is_current
            FROM bronze_candidates
        """)

    # Convert result to a Pandas DataFrame then to Parquet bytes for upload
    result_df = con.execute("SELECT * FROM silver_candidates").df()
    
    # We save to a temp file to upload
    temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    result_df.to_parquet(temp_out.name, index=False)
    
    return temp_out.name

@task
def upload_silver_to_lake(file_path):
    """Uploads the silver parquet file back to Azure."""
    logger = get_run_logger()
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container="silver", blob="candidates_scd2.parquet")
    
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    
    # Clean up the temp file
    os.remove(file_path)
    logger.info("☁️ Silver Layer (SCD Type 2) successfully updated in Azure Lake.")

@flow(name="Silver-Transformation-Pipeline")
def silver_transformation_flow():
    logger = get_run_logger()
    logger.info("🚀 Starting Silver Transformation (SCD Type 2)...")

    # 1. Download Bronze to temp file
    bronze_path = download_parquet_to_temp("bronze", "candidates.parquet")
    
    # 2. Try to download existing Silver to temp file
    silver_path = None
    try:
        silver_path = download_parquet_to_temp("silver", "candidates_scd2.parquet")
    except:
        logger.info("No existing silver data found. Performing initial load.")

    # 3. Apply SCD Logic (takes paths, returns a path)
    silver_result_path = apply_scd_type2_logic(bronze_path, silver_path)

    # 4. Upload the resulting file
    upload_silver_to_lake(silver_result_path)
    
    # Clean up bronze temp file
    if os.path.exists(bronze_path): os.remove(bronze_path)
    if silver_path and os.path.exists(silver_path): os.remove(silver_path)
    
    logger.info("🏁 Silver Layer Transformation Complete!")

if __name__ == "__main__":
    silver_transformation_flow()