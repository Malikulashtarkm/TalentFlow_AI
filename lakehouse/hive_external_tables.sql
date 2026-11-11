-- TalentFlow AI lakehouse external tables.
-- Replace ${LAKE_ROOT} with your storage root, for example:
-- abfss://talentflow@<storage-account>.dfs.core.windows.net
--
-- Runtime folders are partitioned as:
-- bronze/<table_name>/run_datetime=YYYYMMDD_HHMMSS/*.parquet
-- silver/<table_name>/run_datetime=YYYYMMDD_HHMMSS/*.parquet
-- gold/<table_name>/run_datetime=YYYYMMDD_HHMMSS/*.parquet
--
-- After each pipeline run, register new partitions with:
-- MSCK REPAIR TABLE <table_name>;
-- or ALTER TABLE <table_name> ADD PARTITION (...) LOCATION ...;

CREATE DATABASE IF NOT EXISTS talentflow_bronze;
CREATE DATABASE IF NOT EXISTS talentflow_silver;
CREATE DATABASE IF NOT EXISTS talentflow_gold;

-- Bronze external tables

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_bronze.candidates (
    candidate_id STRING,
    email STRING,
    password STRING,
    first_name STRING,
    last_name STRING,
    phone_number STRING,
    city STRING,
    state STRING,
    country STRING,
    expected_salary DECIMAL(18,2),
    created_at TIMESTAMP
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/bronze/candidates';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_bronze.candidate_education (
    edu_id INT,
    candidate_id STRING,
    degree STRING,
    university STRING,
    passing_year INT,
    gpa DECIMAL(5,2)
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/bronze/candidate_education';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_bronze.jobs (
    job_id STRING,
    job_title STRING,
    department STRING,
    salary_range STRING,
    job_location STRING,
    created_at TIMESTAMP
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/bronze/jobs';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_bronze.interview_schedules (
    schedule_id STRING,
    candidate_id STRING,
    job_id STRING,
    interviewer_id STRING,
    stage_id INT,
    interview_date TIMESTAMP,
    status STRING
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/bronze/interview_schedules';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_bronze.interview_feedback (
    feedback_id INT,
    schedule_id STRING,
    rating INT,
    comments STRING,
    decision STRING,
    submitted_at TIMESTAMP
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/bronze/interview_feedback';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_bronze.login_logs (
    log_id INT,
    candidate_id STRING,
    login_timestamp TIMESTAMP
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/bronze/login_logs';

-- Silver external tables

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_silver.candidates_secure (
    candidate_id STRING,
    email STRING,
    password STRING,
    first_name STRING,
    last_name STRING,
    phone_number STRING,
    city STRING,
    state STRING,
    country STRING,
    expected_salary STRING,
    created_at TIMESTAMP,
    row_hash STRING,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_current BOOLEAN
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/silver/candidates_secure';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_silver.candidate_education (
    edu_id INT,
    candidate_id STRING,
    degree STRING,
    university STRING,
    passing_year INT,
    gpa DECIMAL(5,2)
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/silver/candidate_education';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_silver.jobs (
    job_id STRING,
    job_title STRING,
    department STRING,
    salary_range STRING,
    job_location STRING,
    created_at TIMESTAMP
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/silver/jobs';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_silver.interview_schedules (
    schedule_id STRING,
    candidate_id STRING,
    job_id STRING,
    interviewer_id STRING,
    stage_id INT,
    interview_date TIMESTAMP,
    status STRING
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/silver/interview_schedules';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_silver.interview_feedback (
    feedback_id INT,
    schedule_id STRING,
    rating INT,
    comments STRING,
    decision STRING,
    submitted_at TIMESTAMP
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/silver/interview_feedback';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_silver.login_logs (
    log_id INT,
    candidate_id STRING,
    login_timestamp TIMESTAMP
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/silver/login_logs';

-- Gold external tables

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_gold.city_talent_score (
    city STRING,
    candidate_count BIGINT,
    avg_salary DOUBLE
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/gold/city_talent_score';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_gold.salary_benchmarks (
    degree STRING,
    avg_expected DOUBLE
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/gold/salary_benchmarks';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_gold.candidate_engagement (
    candidate_id STRING,
    login_count BIGINT
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/gold/candidate_engagement';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_gold.interview_pipeline_funnel (
    job_title STRING,
    stage_name STRING,
    status STRING,
    interview_count BIGINT
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/gold/interview_pipeline_funnel';

CREATE EXTERNAL TABLE IF NOT EXISTS talentflow_gold.job_hire_rate (
    job_title STRING,
    total_feedback BIGINT,
    hire_count BIGINT,
    hire_rate_pct DOUBLE
)
PARTITIONED BY (run_datetime STRING)
STORED AS PARQUET
LOCATION '${LAKE_ROOT}/gold/job_hire_rate';
