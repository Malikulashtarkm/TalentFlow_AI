import azure.functions as func
import logging
import os
import pandas as pd
from sqlalchemy import create_engine
from azure.storage.blob import BlobServiceClient
from cryptography.fernet import Fernet

# --- SECURITY CONFIG ---
# These will be loaded from Azure "Application Settings" later
def get_secrets():
    return {
        "db_user": os.environ.get("DB_USER"),
        "db_pass": os.environ.get("DB_PASS"),
        "db_host": os.environ.get("DB_HOST"),
        "db_port": os.environ.get("DB_PORT"),
        "db_name": os.environ.get("DB_NAME"),
        "storage_conn": os.environ.get("AZURE_STORAGE_CONNECTION_STRING"),
        "odin_key": os.environ.get("ODIN_KEY")
    }

def odin_encrypt(plain_text, key):
    if plain_text is None: return None
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(str(plain_text).encode()).decode()

# The Main Function
app = func.FunctionApp()

@app.route(route="BronzeIngestion", auth_level=func.AuthLevel.FUNCTION)
def BronzeIngestion(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        secrets = get_secrets()
        # 1. Database Connection
        pg_url = f"postgresql://{secrets['db_user']}:{secrets['db_pass']}@{secrets['db_host']}:{secrets['db_port']}/{secrets['db_name']}"
        engine = create_engine(pg_url)
        
        # 2. Storage Connection
        blob_service_client = BlobServiceClient.from_connection_string(secrets['storage_conn'])
        
        # 3. Define Tables and which columns need encryption
        # Table Name : [List of PII columns to encrypt]
        secure_map = {
            "candidates": ["email", "phone_number"],
            "recruiters": ["email"],
            "interviewers": ["email"],
            # All other tables (jobs, schedules, etc.) have empty lists because they have no PII
            "candidate_education": [],
            "login_logs": [],
            "interview_feedback": [],
            "interview_schedules": [],
            "questions_bank": [],
            "interview_stages": []
        }

        for table, pii_cols in secure_map.items():
            logging.info(f"Processing table: {table}...")
            
            # Extract
            df = pd.read_sql(f"SELECT * FROM {table}", engine)
            
            # Encrypt only if the table has PII columns defined in our map
            if pii_cols:
                logging.info(f"🔐 Encrypting PII in {table}...")
                for col in pii_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: odin_encrypt(x, secrets['odin_key'].encode()))
            
            # Convert to Parquet and upload to Azure Lake
            parquet_buffer = df.to_parquet(index=False)
            blob_client = blob_service_client.get_blob_client(container="bronze", blob=f"{table}.parquet")
            blob_client.upload_blob(parquet_buffer, overwrite=True)
            
            logging.info(f"✅ {table} successfully pushed to Bronze Lake.")

        return func.HttpResponse("✅ ALL TABLES SECURELY INGESTED TO BRONZE LAKE!", status_code=200)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(f"❌ Pipeline Failed: {str(e)}", status_code=500)
