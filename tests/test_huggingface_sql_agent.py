import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import huggingface_sql_agent
from huggingface_sql_agent import _build_prompt, _build_repair_prompt, _parse_plan


def test_huggingface_prompt_contains_safety_rules_and_schema():
    prompt = _build_prompt(
        "Which candidates were hired?",
        "public.candidates: candidate_id uuid, first_name text",
        [],
    )

    assert "PostgreSQL SELECT query" in prompt
    assert "Never select password" in prompt
    assert "public.candidates" in prompt
    assert "Which candidates were hired?" in prompt


def test_repair_prompt_contains_failed_sql_and_error_context():
    prompt = _build_repair_prompt(
        "Which jobs failed?",
        "public.jobs: job_id uuid, job_title text",
        "SELECT missing_col FROM jobs",
        "column missing_col does not exist",
        [],
    )

    assert "text-to-SQL repair agent" in prompt
    assert "SELECT missing_col FROM jobs" in prompt
    assert "column missing_col does not exist" in prompt


def test_langchain_mode_label_is_visible_when_generation_succeeds(monkeypatch):
    monkeypatch.setattr(
        huggingface_sql_agent,
        "_generate_text",
        lambda prompt: '{"title":"Jobs","sql":"SELECT job_title FROM jobs","chart_type":"table","reasoning":"direct lookup"}',
    )

    plan = huggingface_sql_agent.generate_huggingface_sql_plan(
        "Show jobs",
        "public.jobs: job_title text",
        [],
    )

    assert plan["mode"] == "LangChain + Hugging Face local LLM"
    assert plan["sql"] == "SELECT * FROM (\nSELECT job_title FROM jobs\n) AS talentflow_agent_result\nLIMIT 100"


def test_huggingface_plan_parser_accepts_json_output():
    plan = _parse_plan(
        '{"title":"Hired candidates","sql":"SELECT first_name FROM candidates","chart_type":"table","reasoning":"direct lookup"}'
    )

    assert plan["title"] == "Hired candidates"
    assert plan["sql"] == "SELECT first_name FROM candidates"
    assert plan["chart_type"] == "table"


def test_huggingface_plan_parser_accepts_sql_fence_output():
    plan = _parse_plan("```sql\nSELECT job_title FROM jobs\n```")

    assert plan["title"] == "Local LLM answer"
    assert plan["sql"] == "SELECT job_title FROM jobs"
