import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from genai_agent_orchestrator import route_prompt, run_genai_agent_team, serialize_agent_run


def test_router_selects_relevant_agents_and_always_adds_risk():
    route = route_prompt("Create interview questions and check bias risk")

    assert "interview" in route
    assert "risk" in route


def test_multi_agent_run_returns_trace_artifacts_and_guardrails():
    run = run_genai_agent_team(
        "Create outreach, interview questions, hiring summary data, and privacy review for alex@example.com",
        candidate={"first_name": "Alex", "degree": "M.Tech", "city": "Bengaluru"},
        job={"job_title": "GenAI Engineer", "department": "AI", "job_location": "Bengaluru"},
        stage_name="Technical",
        feedback_rows=[{"rating": 5, "comments": "Strong SQL and LLM reasoning.", "decision": "Hire"}],
    )

    serialized = serialize_agent_run(run)

    assert run.run_type == "multi_agent_genai_workflow"
    assert run.guardrail_score >= 80
    assert "job_description" in run.artifacts
    assert "interview_kit" in run.artifacts
    assert "risk_report" in run.artifacts
    assert "[email]" in serialized["trace"][0]["metadata"]["redacted_prompt"]
    assert any(event["agent_name"] == "risk_agent" for event in serialized["trace"])


def test_analytics_agent_produces_safe_plan_for_known_kpi_request():
    run = run_genai_agent_team("Give me a hiring summary with KPIs")

    plan = run.artifacts["analytics_plan"]

    assert plan["requires_execution"] is True
    assert plan["sql"].lower().startswith("select")
    assert "password" not in plan["sql"].lower()
