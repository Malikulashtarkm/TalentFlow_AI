import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("config/.env")

try:
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        port=os.environ.get("DB_PORT")
    )
    print("✅ Success! Connected to Azure PostgreSQL.")
    conn.close()
except Exception as e:
    print(f"❌ Connection Failed: {e}")
