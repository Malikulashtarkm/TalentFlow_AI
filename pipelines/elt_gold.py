import os
import sys
import pandas as pd
import duckdb
import tempfile
import argparse
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from sqlalchemy import create_engine, text
from prefect import flow, task, get_run_logger

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "utils"))

from crypto_utils import odin_decrypt
from run_context import latest_blob, make_run_datetime, versioned_blob

load_dotenv(os.path.join(project_root, "config", ".env"))

STORAGE_CONN = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")

if not all([STORAGE_CONN, DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME]):
    raise EnvironmentError("Missing required environment variables in config/.env")

PG_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def _decrypt_salary(value) -> float:
    if value is None:
        return 0.0
    decrypted = odin_decrypt(value)
    if decrypted and not str(decrypted).startswith("DECRYPTION_ERROR"):
        try:
            return float(decrypted)
        except ValueError:
            return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _temp_parquet_path() -> str:
    fd, path = tempfile.mkstemp(suffix=".parquet")
    os.close(fd)
    return path


def _upload_to_gold(file_path: str, blob_name: str, run_datetime: str):
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONN)
    for target_blob in [versioned_blob(run_datetime, blob_name), latest_blob(blob_name)]:
        blob_client = blob_service_client.get_blob_client(
            container="gold",
            blob=target_blob,
        )
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)


@task
def download_silver_parquet(blob_name: str, label: str, run_datetime: str) -> tuple[str, str]:
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONN)
    blob_client = blob_service_client.get_blob_client(
        container="silver",
        blob=versioned_blob(run_datetime, blob_name),
    )
    path = _temp_parquet_path()
    with open(path, "wb") as f:
        f.write(blob_client.download_blob().readall())
    return label, path


@task
def download_silver_data(run_datetime: str):
    logger = get_run_logger()
    logger.info(f"Downloading silver layer data for gold run {run_datetime}...")

    downloads = [
        ("candidates_secure.parquet", "candidates"),
        ("candidate_education.parquet", "education"),
        ("login_logs.parquet", "logins"),
        ("interview_schedules.parquet", "schedules"),
        ("interview_feedback.parquet", "feedback"),
        ("jobs.parquet", "jobs"),
        ("interview_stages.parquet", "stages"),
    ]

    temp_files = {}
    for blob_name, label in downloads:
        _, path = download_silver_parquet(blob_name, label, run_datetime)
        temp_files[label] = path

    return temp_files


@task
def calculate_gold_metrics(paths):
    logger = get_run_logger()
    logger.info("Calculating gold KPIs via DuckDB...")

    df_candidates = pd.read_parquet(paths["candidates"])
    df_candidates["expected_salary_decrypted"] = df_candidates.get(
        "expected_salary", pd.Series(dtype=object)
    ).apply(_decrypt_salary)

    con = duckdb.connect(database=":memory:")
    con.execute("CREATE TABLE candidates AS SELECT * FROM df_candidates")
    con.execute(f"CREATE TABLE education AS SELECT * FROM read_parquet('{paths['education']}')")
    con.execute(f"CREATE TABLE logins AS SELECT * FROM read_parquet('{paths['logins']}')")
    con.execute(f"CREATE TABLE schedules AS SELECT * FROM read_parquet('{paths['schedules']}')")
    con.execute(f"CREATE TABLE feedback AS SELECT * FROM read_parquet('{paths['feedback']}')")
    con.execute(f"CREATE TABLE jobs AS SELECT * FROM read_parquet('{paths['jobs']}')")
    con.execute(f"CREATE TABLE stages AS SELECT * FROM read_parquet('{paths['stages']}')")

    city_score = con.execute("""
        SELECT city, COUNT(*) AS candidate_count, AVG(expected_salary_decrypted) AS avg_salary
        FROM candidates
        WHERE is_current = TRUE
        GROUP BY city
    """).df()

    salary_bench = con.execute("""
        SELECT e.degree, AVG(c.expected_salary_decrypted) AS avg_expected
        FROM candidates c
        JOIN education e ON c.candidate_id = e.candidate_id
        WHERE c.is_current = TRUE
        GROUP BY e.degree
    """).df()

    engagement = con.execute("""
        SELECT candidate_id, COUNT(*) AS login_count
        FROM logins
        GROUP BY candidate_id
    """).df()

    pipeline_funnel = con.execute("""
        SELECT j.job_title, st.stage_name, s.status, COUNT(*) AS interview_count
        FROM schedules s
        JOIN jobs j ON s.job_id = j.job_id
        JOIN stages st ON s.stage_id = st.stage_id
        GROUP BY j.job_title, st.stage_name, s.status
    """).df()

    hire_rate = con.execute("""
        SELECT j.job_title,
               COUNT(*) AS total_feedback,
               SUM(CASE WHEN f.decision = 'Hire' THEN 1 ELSE 0 END) AS hire_count,
               ROUND(100.0 * SUM(CASE WHEN f.decision = 'Hire' THEN 1 ELSE 0 END) / COUNT(*), 2) AS hire_rate_pct
        FROM feedback f
        JOIN schedules s ON f.schedule_id = s.schedule_id
        JOIN jobs j ON s.job_id = j.job_id
        GROUP BY j.job_title
    """).df()

    return {
        "city_score": city_score,
        "salary_bench": salary_bench,
        "engagement": engagement,
        "pipeline_funnel": pipeline_funnel,
        "hire_rate": hire_rate,
    }


@task
def load_to_postgres_gold(metrics):
    logger = get_run_logger()
    engine = create_engine(PG_URL)

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))

    table_map = {
        "city_score": "city_talent_score",
        "salary_bench": "salary_benchmarks",
        "engagement": "candidate_engagement",
        "pipeline_funnel": "interview_pipeline_funnel",
        "hire_rate": "job_hire_rate",
    }

    for key, table_name in table_map.items():
        metrics[key].to_sql(table_name, engine, schema="analytics", if_exists="replace", index=False)

    logger.info("Gold layer pushed to Azure PostgreSQL (analytics schema).")


@task
def upload_gold_snapshots(metrics, run_datetime: str):
    logger = get_run_logger()
    table_map = {
        "city_score": "city_talent_score.parquet",
        "salary_bench": "salary_benchmarks.parquet",
        "engagement": "candidate_engagement.parquet",
        "pipeline_funnel": "interview_pipeline_funnel.parquet",
        "hire_rate": "job_hire_rate.parquet",
    }

    temp_paths = []
    try:
        for key, blob_name in table_map.items():
            path = _temp_parquet_path()
            metrics[key].to_parquet(path, index=False)
            temp_paths.append(path)
            _upload_to_gold(path, blob_name, run_datetime)
        logger.info(f"Gold parquet snapshots uploaded for run {run_datetime}.")
    finally:
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)


@flow(name="Gold-Analytical-Flow")
def gold_flow(run_datetime: str | None = None, publish_postgres: bool = False):
    run_datetime = run_datetime or make_run_datetime()
    logger = get_run_logger()
    logger.info(f"Starting gold layer aggregation for run {run_datetime}...")

    paths = download_silver_data(run_datetime)
    metrics = calculate_gold_metrics(paths)
    upload_gold_snapshots(metrics, run_datetime)
    if publish_postgres:
        load_to_postgres_gold(metrics)
    else:
        logger.info("Skipping PostgreSQL publish; gold parquet is the analytical source of truth.")

    for p in paths.values():
        if os.path.exists(p):
            os.remove(p)

    logger.info("Gold layer transformation complete.")
    return run_datetime


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build gold analytics parquet snapshots from silver lake data."
    )
    parser.add_argument(
        "--publish-postgres",
        action="store_true",
        help="Also publish gold tables into the PostgreSQL analytics schema for dashboard caching.",
    )
    args = parser.parse_args()
    gold_flow(publish_postgres=args.publish_postgres)
