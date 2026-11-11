import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from local_sql_model import generate_local_sql_plan


def test_local_model_handles_high_rated_not_hired_question():
    plan = generate_local_sql_plan("Which candidates have high ratings but were not hired?")

    assert plan["mode"] == "Local model"
    assert plan["title"] == "High-rated candidates not hired"
    assert "HAVING AVG(f.rating) >= 4" in plan["sql"]
    assert "LOWER(f.decision) = 'hire'" in plan["sql"]


def test_local_model_handles_interviewer_assignment_question():
    plan = generate_local_sql_plan("Who is the interviewer interviewing?")

    assert plan["title"] == "Interviewer assignments"
    assert "FROM interview_schedules" in plan["sql"]
    assert "JOIN interviewers" in plan["sql"]
    assert "candidate" in plan["sql"]


def test_local_model_handles_degree_performance_question():
    plan = generate_local_sql_plan("Which degrees are associated with better ratings?")

    assert plan["title"] == "Degrees associated with better ratings"
    assert "candidate_education" in plan["sql"]
    assert "AVG(f.rating)" in plan["sql"]


def test_local_model_can_reuse_learned_corrected_sql():
    learned = [
        {
            "question": "Which recruiters own west region jobs?",
            "generated_sql": None,
            "corrected_sql": "SELECT full_name, region FROM recruiters WHERE region = 'West'",
            "chart_type": "table",
        }
    ]
    plan = generate_local_sql_plan("Show west region recruiters", learned)

    assert plan["title"] == "Learned answer"
    assert "FROM recruiters" in plan["sql"]
