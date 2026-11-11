import json
import re
from datetime import datetime, timezone


SKILL_KEYWORDS = {
    "python": "Python",
    "sql": "SQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "azure": "Azure",
    "blob": "Azure Blob Storage",
    "duckdb": "DuckDB",
    "prefect": "Prefect",
    "streamlit": "Streamlit",
    "ml": "Machine learning",
    "machine learning": "Machine learning",
    "genai": "Generative AI",
    "llm": "LLM application design",
    "rag": "Retrieval augmented generation",
    "etl": "ELT pipelines",
    "elt": "ELT pipelines",
    "api": "API integration",
    "analytics": "Analytics engineering",
    "dashboard": "Dashboard development",
}

DEFAULT_COMPETENCIES = [
    "problem decomposition",
    "data modeling",
    "production debugging",
    "communication",
]

SENSITIVE_PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[email]"),
    (re.compile(r"\b(?:\+?\d[\s-]?){8,15}\b"), "[phone]"),
    (re.compile(r"\b\d{4,}\s*(?:lpa|lakhs?|usd|inr|rs\.?)\b", re.IGNORECASE), "[compensation]"),
]


def ensure_genai_tables(cur):
    cur.execute("CREATE SCHEMA IF NOT EXISTS analytics")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analytics.genai_copilot_outputs (
            output_id SERIAL PRIMARY KEY,
            user_email TEXT,
            artifact_type TEXT NOT NULL,
            prompt_context JSONB,
            generated_content TEXT NOT NULL,
            guardrail_notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_genai_copilot_outputs_created_at
        ON analytics.genai_copilot_outputs(created_at DESC)
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analytics.genai_agent_runs (
            run_id SERIAL PRIMARY KEY,
            user_email TEXT,
            run_type TEXT NOT NULL,
            prompt TEXT,
            agent_trace JSONB,
            final_answer TEXT,
            guardrail_score INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_genai_agent_runs_created_at
        ON analytics.genai_agent_runs(created_at DESC)
        """
    )


def redact_sensitive_text(text):
    cleaned = str(text or "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


def extract_skills(*texts):
    joined = " ".join(str(text or "").lower() for text in texts)
    skills = []
    for token, label in SKILL_KEYWORDS.items():
        if token in joined and label not in skills:
            skills.append(label)
    return skills[:8]


def generate_job_description(job):
    title = _value(job, "job_title", "GenAI engineer")
    department = _value(job, "department", "AI engineering")
    location = _value(job, "job_location", "hybrid")
    salary_range = _value(job, "salary_range", "market aligned")
    skills = extract_skills(title, department, location) or [
        "Python",
        "SQL",
        "LLM application design",
        "production data systems",
    ]

    return _join_sections(
        f"Role: {title}",
        f"Department: {department}",
        f"Location: {location}",
        f"Compensation: {salary_range}",
        "Summary: Build practical AI features for hiring teams, combining reliable data pipelines, analytics, and guarded generative workflows.",
        "Responsibilities:\n"
        "- Design LLM-assisted hiring workflows for job descriptions, interview kits, feedback summaries, and analytics Q&A.\n"
        "- Connect GenAI outputs to trusted recruitment data instead of unsupported free-form guesses.\n"
        "- Add safety checks for PII, SQL access, and biased or unsupported hiring recommendations.\n"
        "- Partner with recruiters, interviewers, and data engineers to measure quality and improve prompts over time.",
        "Required skills:\n" + "\n".join(f"- {skill}" for skill in skills),
        "Evaluation focus: candidate experience, measurable recruiter productivity, explainability, and safe use of sensitive hiring data.",
    )


def generate_outreach_message(candidate, job):
    first_name = _value(candidate, "first_name", "there")
    title = _value(job, "job_title", "the role")
    location = _value(job, "job_location", "our team")
    degree = _value(candidate, "degree", "your background")
    city = _value(candidate, "city", "your location")

    return _join_sections(
        f"Hi {first_name},",
        (
            f"I noticed your profile includes {degree} experience from {city}, and it looks relevant "
            f"for our {title} opening in {location}."
        ),
        (
            "TalentFlow AI is using a guarded GenAI copilot to help recruiters draft personalized outreach, "
            "but the final message is reviewed by a human before sending."
        ),
        "Would you be open to a short conversation about the role and the interview process?",
        "Best,\nTalentFlow recruiting team",
    )


def generate_interview_kit(job, stage_name, candidate=None, count=5):
    title = _value(job, "job_title", "GenAI engineer")
    stage = stage_name or "Technical"
    candidate_context = ""
    if candidate:
        candidate_context = f" Candidate context: {_value(candidate, 'degree', 'profile')} from {_value(candidate, 'city', 'listed city')}."

    skills = extract_skills(title, stage, candidate_context) or [
        "Python",
        "SQL",
        "LLM application design",
        "data pipeline reasoning",
        "responsible AI",
    ]
    competencies = skills[:3] + DEFAULT_COMPETENCIES
    questions = []
    for index, competency in enumerate(competencies[:count], start=1):
        questions.append(
            {
                "question": (
                    f"{index}. For a {title} {stage} round, describe a project where you applied "
                    f"{competency}. What tradeoffs did you make and how did you validate the result?"
                ),
                "rubric": (
                    "Strong answer: gives a concrete system, explains data or prompt quality, names failure modes, "
                    "and connects the work to a measurable hiring or product outcome."
                ),
            }
        )
    return questions


def summarize_feedback(feedback_rows):
    rows = [dict(row) for row in feedback_rows or []]
    if not rows:
        return "No interview feedback has been submitted yet. Suggested next action: collect interviewer notes before making a decision."

    ratings = [row.get("rating") for row in rows if isinstance(row.get("rating"), int)]
    decisions = [str(row.get("decision") or "Not specified") for row in rows]
    comments = " ".join(redact_sensitive_text(row.get("comments", "")) for row in rows)
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else "not available"
    positive_terms = _matched_terms(comments, {"strong", "clear", "good", "excellent", "hire", "solid"})
    risk_terms = _matched_terms(comments, {"weak", "unclear", "concern", "reject", "gap", "slow"})

    return _join_sections(
        f"Feedback summary: {len(rows)} feedback record(s), average rating {avg_rating}.",
        f"Decision signals: {', '.join(decisions)}.",
        f"Strength signals: {', '.join(positive_terms) if positive_terms else 'No repeated positive signal found in comments.'}",
        f"Risk signals: {', '.join(risk_terms) if risk_terms else 'No repeated risk signal found in comments.'}",
        "Suggested next action: make the final decision from the structured rating, role requirements, and human review notes; do not use generated text as the sole hiring basis.",
    )


def build_copilot_pack(candidate, job, stage_name, feedback_rows=None):
    redacted_candidate = {
        key: redact_sensitive_text(value)
        for key, value in dict(candidate or {}).items()
        if key not in {"password", "phone_number", "email"}
    }
    context = {
        "candidate": redacted_candidate,
        "job": dict(job or {}),
        "stage_name": stage_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    interview_kit = generate_interview_kit(job, stage_name, redacted_candidate)
    return {
        "job_description": generate_job_description(job),
        "candidate_outreach": generate_outreach_message(redacted_candidate, job),
        "interview_kit": interview_kit,
        "feedback_summary": summarize_feedback(feedback_rows),
        "guardrail_notes": (
            "PII is redacted from prompt context, password/email/phone are excluded, "
            "and generated hiring text requires human review."
        ),
        "context": context,
    }


def record_copilot_output(cur, user_email, artifact_type, prompt_context, generated_content, guardrail_notes):
    ensure_genai_tables(cur)
    cur.execute(
        """
        INSERT INTO analytics.genai_copilot_outputs
            (user_email, artifact_type, prompt_context, generated_content, guardrail_notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING output_id
        """,
        (
            user_email,
            artifact_type,
            json.dumps(prompt_context, default=str),
            generated_content,
            guardrail_notes,
        ),
    )
    return cur.fetchone()["output_id"]


def record_agent_run(cur, user_email, prompt, serialized_run):
    ensure_genai_tables(cur)
    cur.execute(
        """
        INSERT INTO analytics.genai_agent_runs
            (user_email, run_type, prompt, agent_trace, final_answer, guardrail_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING run_id
        """,
        (
            user_email,
            serialized_run["run_type"],
            redact_sensitive_text(prompt),
            json.dumps(serialized_run["trace"], default=str),
            serialized_run["final_answer"],
            serialized_run["guardrail_score"],
        ),
    )
    return cur.fetchone()["run_id"]


def _value(row, key, fallback):
    if not row:
        return fallback
    value = dict(row).get(key)
    return str(value).strip() if value else fallback


def _join_sections(*sections):
    return "\n\n".join(section.strip() for section in sections if section and section.strip())


def _matched_terms(text, vocabulary):
    lowered = (text or "").lower()
    return sorted(term for term in vocabulary if re.search(rf"\b{re.escape(term)}\b", lowered))
