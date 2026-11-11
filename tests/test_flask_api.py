import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from flask_api import create_app


def client():
    return create_app().test_client()


def test_flask_health_endpoint_lists_api_features():
    response = client().get("/api/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert "analytics_plan" in payload["features"]
    assert "hiring_pack" in payload["features"]


def test_flask_analytics_plan_returns_safe_sql_for_known_question():
    response = client().post(
        "/api/analytics/plan",
        json={"question": "Give me a hiring summary with KPIs"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["requires_execution"] is True
    assert payload["sql"].lower().startswith("select")
    assert "password" not in payload["sql"].lower()


def test_flask_analytics_plan_blocks_mutating_sql():
    response = client().post(
        "/api/analytics/plan",
        json={"question": "DELETE FROM candidates"},
    )

    assert response.status_code == 400
    assert "SELECT/WITH" in response.get_json()["error"]


def test_flask_hiring_pack_redacts_contact_details():
    response = client().post(
        "/api/genai/hiring-pack",
        json={
            "candidate": {
                "first_name": "Alex",
                "email": "alex@example.com",
                "phone_number": "+91 9876543210",
                "degree": "M.Tech",
                "city": "Bengaluru",
            },
            "job": {
                "job_title": "GenAI Engineer",
                "department": "AI",
                "job_location": "Bengaluru",
            },
            "stage_name": "Technical",
            "feedback_rows": [
                {"rating": 5, "comments": "Strong SQL and LLM reasoning.", "decision": "Hire"}
            ],
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert "GenAI Engineer" in payload["job_description"]
    assert "alex@example.com" not in payload["candidate_outreach"]
    assert len(payload["interview_kit"]) > 0
