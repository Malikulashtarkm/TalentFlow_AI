import os
import json
import sys
import time
import psycopg2
from dotenv import load_dotenv

# #region agent log
def _agent_log(hypothesis_id, location, message, data):
    try:
        entry = {
            "id": f"log_{int(time.time() * 1000)}_{hypothesis_id}",
            "timestamp": int(time.time() * 1000),
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "runId": os.environ.get("DEBUG_RUN_ID", "pre-fix"),
        }
        with open(r"d:\TalentFlow_AI\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
# #endregion

# #region agent log
_agent_log("H4", "test_azure_conn.py:startup", "Interpreter started", {
    "executable": sys.executable,
    "version": sys.version.split()[0],
})
# #endregion

# 1. Load secrets
load_dotenv("config/.env")

# #region agent log
_agent_log("H6", "test_azure_conn.py:env", "Env loaded (no secrets)", {
    "env_file_exists": os.path.isfile("config/.env"),
    "db_host_set": bool(os.environ.get("DB_HOST")),
    "db_host_placeholder": os.environ.get("DB_HOST", "").startswith("your-server"),
})
# #endregion

try:
    # 2. Connect to Azure PostgreSQL
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