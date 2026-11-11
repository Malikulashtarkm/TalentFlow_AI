import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from analytics_agent import _extract_response_text, _fallback_narrative, _terms


def test_extract_response_text_supports_responses_payload():
    payload = {
        "output": [
            {
                "content": [
                    {"type": "output_text", "text": "{\"sql\":\"SELECT 1\"}"},
                ]
            }
        ]
    }

    assert _extract_response_text(payload) == "{\"sql\":\"SELECT 1\"}"


def test_fallback_narrative_summarizes_single_row_metrics():
    rows = [{"total_candidates": 10, "open_roles": 4}]
    summary = _fallback_narrative(rows, {"title": "Hiring summary"})

    assert "total candidates = 10" in summary
    assert "open roles = 4" in summary


def test_terms_remove_question_noise_words():
    assert "interviewers" in _terms("Which interviewers have pending feedback?")
    assert "which" not in _terms("Which interviewers have pending feedback?")
