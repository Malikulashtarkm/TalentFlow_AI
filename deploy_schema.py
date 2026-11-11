import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DDL_PATH = ROOT / "DDL.sql"

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(ROOT / "config" / ".env")

MIGRATION_SQL = """
DO $$ BEGIN
    ALTER TABLE candidates ADD COLUMN password TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE candidates ADD COLUMN expected_salary NUMERIC;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""


def read_schema_sql():
    return DDL_PATH.read_text(encoding="utf-8")


def deploy():
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            port=os.environ.get("DB_PORT"),
        )
        cur = conn.cursor()

        print("Deploying schema to Azure PostgreSQL...")
        cur.execute(read_schema_sql())
        cur.execute(MIGRATION_SQL)
        conn.commit()

        print("Success! Tables, indexes, analytics schema, and agent memory are ready.")
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Deployment failed: {e}")


if __name__ == "__main__":
    deploy()
