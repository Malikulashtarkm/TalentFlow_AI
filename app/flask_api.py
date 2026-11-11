from flask import Flask, jsonify, request

from analytics_assistant import BLOCKED_SQL_WORDS, build_assistant_sql, schema_markdown
from genai_hiring_copilot import build_copilot_pack, redact_sensitive_text


DEFAULT_STAGE_NAME = "Technical"


def create_app():
    app = Flask(__name__)

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "service": "TalentFlow AI API",
                "status": "ok",
                "features": ["analytics_plan", "schema_guide", "hiring_pack"],
            }
        )

    @app.get("/api/analytics/schema")
    def analytics_schema():
        return jsonify({"schema_markdown": schema_markdown()})

    @app.post("/api/analytics/plan")
    def analytics_plan():
        payload = request.get_json(silent=True) or {}
        question = str(payload.get("question") or "").strip()
        if not question:
            return jsonify({"error": "question is required"}), 400

        if _contains_blocked_sql_word(question):
            return jsonify({"error": "Only SELECT/WITH queries are allowed in the API."}), 400

        try:
            sql, title = build_assistant_sql(question)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        if not sql:
            return jsonify({"title": title, "sql": None, "requires_execution": False}), 422

        return jsonify(
            {
                "title": title,
                "sql": sql,
                "requires_execution": True,
                "safety": "Read-only SELECT/WITH SQL; blocked mutating SQL and password fields.",
            }
        )

    @app.post("/api/genai/hiring-pack")
    def hiring_pack():
        payload = request.get_json(silent=True) or {}
        candidate = payload.get("candidate") or {}
        job = payload.get("job") or {}
        stage_name = payload.get("stage_name") or DEFAULT_STAGE_NAME
        feedback_rows = payload.get("feedback_rows") or []

        if not isinstance(candidate, dict) or not isinstance(job, dict):
            return jsonify({"error": "candidate and job must be objects"}), 400
        if not isinstance(feedback_rows, list):
            return jsonify({"error": "feedback_rows must be a list"}), 400

        pack = build_copilot_pack(candidate, job, stage_name, feedback_rows)
        return jsonify(
            {
                "job_description": pack["job_description"],
                "candidate_outreach": redact_sensitive_text(pack["candidate_outreach"]),
                "interview_kit": pack["interview_kit"],
                "feedback_summary": pack["feedback_summary"],
                "guardrail_notes": pack["guardrail_notes"],
            }
        )

    return app


def _contains_blocked_sql_word(text):
    tokens = set(str(text or "").lower().replace(";", " ").split())
    return bool(BLOCKED_SQL_WORDS.intersection(tokens))


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)


