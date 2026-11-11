import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from genai_hiring_copilot import (
    build_copilot_pack,
    generate_interview_kit,
    redact_sensitive_text,
    summarize_feedback,
)


def test_copilot_redacts_sensitive_contact_details():
    text = "Reach me at alex@example.com or +91 98765 43210."

    redacted = redact_sensitive_text(text)

    assert "alex@example.com" not in redacted
    assert "98765" not in redacted
    assert "[email]" in redacted
    assert "[phone]" in redacted


def test_interview_kit_mentions_role_stage_and_rubric():
    job = {"job_title": "GenAI Engineer", "department": "Data and AI"}

    kit = generate_interview_kit(job, "Technical", count=3)

    assert len(kit) == 3
    assert "GenAI Engineer" in kit[0]["question"]
    assert "Technical" in kit[0]["question"]
    assert "Strong answer" in kit[0]["rubric"]


def test_feedback_summary_keeps_human_review_boundary():
    summary = summarize_feedback(
        [
            {"rating": 5, "comments": "Strong SQL and clear GenAI reasoning.", "decision": "Hire"},
            {"rating": 3, "comments": "Some concern about production debugging.", "decision": "Hold"},
        ]
    )

    assert "average rating 4.0" in summary
    assert "human review" in summary
    assert "strong" in summary.lower()
    assert "concern" in summary.lower()


def test_copilot_pack_excludes_email_phone_password_from_context():
    candidate = {
        "first_name": "Alex",
        "last_name": "Rao",
        "email": "alex@example.com",
        "phone_number": "+91 98765 43210",
        "password": "secret",
        "degree": "M.Tech",
        "city": "Bengaluru",
    }
    job = {"job_title": "GenAI Engineer", "department": "AI", "job_location": "Bengaluru"}

    pack = build_copilot_pack(candidate, job, "Technical")

    assert "email" not in pack["context"]["candidate"]
    assert "phone_number" not in pack["context"]["candidate"]
    assert "password" not in pack["context"]["candidate"]
    assert "human review" in pack["guardrail_notes"]
