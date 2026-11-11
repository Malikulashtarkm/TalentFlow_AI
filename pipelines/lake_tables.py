"""Shared table registry for ADLS Gen2 medallion pipelines."""

BRONZE_TABLES = [
    "jobs",
    "recruiters",
    "interviewers",
    "candidates",
    "candidate_education",
    "candidate_audit_log",
    "interview_stages",
    "questions_bank",
    "interview_schedules",
    "interview_feedback",
    "candidate_responses",
    "login_logs",
]

# These tables need encryption before they move into the silver layer.
PII_TABLES = {
    "candidates": {
        "columns": ["email", "phone_number", "password", "expected_salary"],
        "scd2": True,
        "silver_blob": "candidates_secure.parquet",
    },
    "recruiters": {
        "columns": ["email"],
        "scd2": False,
        "silver_blob": "recruiters_secure.parquet",
    },
    "interviewers": {
        "columns": ["email"],
        "scd2": False,
        "silver_blob": "interviewers_secure.parquet",
    },
    "candidate_audit_log": {
        "columns": ["old_value", "new_value"],
        "scd2": False,
        "silver_blob": "candidate_audit_log_secure.parquet",
    },
}

PASS_THROUGH_TABLES = [t for t in BRONZE_TABLES if t not in PII_TABLES]
