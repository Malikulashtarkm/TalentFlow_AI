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
    cur = conn.cursor()
    cur.execute("ALTER TABLE candidates ADD COLUMN password TEXT;")
    conn.commit()
    print("✅ Password column added to candidates table!")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")