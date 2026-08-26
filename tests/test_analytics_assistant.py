import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from analytics_assistant import build_assistant_sql, sanitize_read_only_sql


def test_natural_language_question_generates_operational_sql():
    sql, label = build_assistant_sql("Which interviewers have pending feedback?")

    assert label == "Interviewer workload"
    assert "FROM interviewers" in sql
    assert "interview_schedules" in sql
    assert "AS talentflow_agent_result" in sql
    assert "LIMIT 100" in sql


def test_custom_read_only_sql_is_allowed_and_limited():
    sql, label = build_assistant_sql("SELECT job_title FROM jobs")

    assert label == "Custom SQL"
    assert "SELECT job_title FROM jobs" in sql
    assert sql.endswith("LIMIT 100")


def test_mutating_sql_is_blocked():
    with pytest.raises(ValueError):
        sanitize_read_only_sql("DELETE FROM candidates")


def test_password_column_is_blocked():
    with pytest.raises(ValueError):
        sanitize_read_only_sql("SELECT email, password FROM candidates")
