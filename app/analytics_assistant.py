import re


BLOCKED_SQL_WORDS = {
    "alter",
    "copy",
    "create",
    "delete",
    "drop",
    "execute",
    "grant",
    "insert",
    "merge",
    "revoke",
    "truncate",
    "update",
}

SENSITIVE_COLUMNS = {"password"}


SCHEMA_GUIDE = {
    "candidates": "Candidate profile, location, salary expectation, signup time",
    "candidate_education": "Degree, university, passing year, GPA",
    "candidate_audit_log": "Profile change history",
    "login_logs": "Candidate engagement and login activity",
    "jobs": "Job title, department, salary range, location",
    "interviewers": "Interviewer directory and specialization",
    "interview_stages": "Hiring stages",
    "interview_schedules": "Candidate-job-interviewer-stage scheduling",
    "interview_feedback": "Ratings, comments, and hire/hold/reject decisions",
    "candidate_responses": "Candidate answers to interview questions",
    "questions_bank": "Question bank by role/category",
    "analytics.*": "Gold KPI tables and ML feature insights when published",
}


QUESTION_PATTERNS = [
    {
        "label": "Hiring summary",
        "keywords": ("summary", "overview", "status", "pipeline"),
        "sql": """
            SELECT
                COUNT(DISTINCT c.candidate_id) AS total_candidates,
                COUNT(DISTINCT j.job_id) AS open_roles,
                COUNT(DISTINCT s.schedule_id) AS scheduled_interviews,
                COUNT(DISTINCT f.feedback_id) AS submitted_feedback,
                COUNT(*) FILTER (WHERE LOWER(f.decision) = 'hire') AS hire_recommendations,
                ROUND(AVG(f.rating)::numeric, 2) AS avg_feedback_rating
            FROM candidates c
            LEFT JOIN interview_schedules s ON s.candidate_id = c.candidate_id
            LEFT JOIN jobs j ON j.job_id = s.job_id
            LEFT JOIN interview_feedback f ON f.schedule_id = s.schedule_id
        """,
    },
    {
        "label": "Candidates by city",
        "keywords": ("city", "cities", "location", "where"),
        "sql": """
            SELECT city, state, country, COUNT(*) AS candidate_count
            FROM candidates
            GROUP BY city, state, country
            ORDER BY candidate_count DESC, city
            LIMIT 25
        """,
    },
    {
        "label": "Highest rated candidates",
        "keywords": ("highest rated", "top candidates", "best candidates", "rating"),
        "sql": """
            SELECT
                c.first_name,
                c.last_name,
                c.city,
                j.job_title,
                ROUND(AVG(f.rating)::numeric, 2) AS avg_rating,
                COUNT(f.feedback_id) AS feedback_count
            FROM candidates c
            JOIN interview_schedules s ON s.candidate_id = c.candidate_id
            JOIN jobs j ON j.job_id = s.job_id
            JOIN interview_feedback f ON f.schedule_id = s.schedule_id
            GROUP BY c.candidate_id, c.first_name, c.last_name, c.city, j.job_title
            ORDER BY avg_rating DESC, feedback_count DESC
            LIMIT 20
        """,
    },
    {
        "label": "Hire decisions by job",
        "keywords": ("hire", "selected", "decision", "job"),
        "sql": """
            SELECT
                j.job_title,
                COUNT(f.feedback_id) AS total_feedback,
                COUNT(*) FILTER (WHERE LOWER(f.decision) = 'hire') AS hire_count,
                COUNT(*) FILTER (WHERE LOWER(f.decision) = 'hold') AS hold_count,
                COUNT(*) FILTER (WHERE LOWER(f.decision) = 'reject') AS reject_count,
                ROUND(100.0 * COUNT(*) FILTER (WHERE LOWER(f.decision) = 'hire') / NULLIF(COUNT(f.feedback_id), 0), 2) AS hire_rate_pct
            FROM jobs j
            LEFT JOIN interview_schedules s ON s.job_id = j.job_id
            LEFT JOIN interview_feedback f ON f.schedule_id = s.schedule_id
            GROUP BY j.job_title
            ORDER BY hire_rate_pct DESC NULLS LAST, total_feedback DESC
        """,
    },
    {
        "label": "Upcoming interviews",
        "keywords": ("upcoming", "scheduled", "interviews", "calendar"),
        "sql": """
            SELECT
                s.interview_date,
                c.first_name,
                c.last_name,
                j.job_title,
                i.full_name AS interviewer,
                st.stage_name,
                s.status
            FROM interview_schedules s
            JOIN candidates c ON c.candidate_id = s.candidate_id
            JOIN jobs j ON j.job_id = s.job_id
            JOIN interviewers i ON i.interviewer_id = s.interviewer_id
            JOIN interview_stages st ON st.stage_id = s.stage_id
            WHERE s.interview_date >= NOW() - INTERVAL '1 day'
            ORDER BY s.interview_date
            LIMIT 30
        """,
    },
    {
        "label": "Candidate engagement",
        "keywords": ("login", "engagement", "active", "activity"),
        "sql": """
            SELECT
                c.first_name,
                c.last_name,
                c.email,
                COUNT(l.log_id) AS login_count,
                MAX(l.login_timestamp) AS latest_login
            FROM candidates c
            LEFT JOIN login_logs l ON l.candidate_id = c.candidate_id
            GROUP BY c.candidate_id, c.first_name, c.last_name, c.email
            ORDER BY login_count DESC, latest_login DESC NULLS LAST
            LIMIT 25
        """,
    },
    {
        "label": "Education profile",
        "keywords": ("degree", "education", "university", "gpa"),
        "sql": """
            SELECT
                e.degree,
                COUNT(*) AS candidate_count,
                ROUND(AVG(e.gpa)::numeric, 2) AS avg_gpa,
                ROUND(AVG(c.expected_salary)::numeric, 2) AS avg_expected_salary
            FROM candidate_education e
            JOIN candidates c ON c.candidate_id = e.candidate_id
            GROUP BY e.degree
            ORDER BY candidate_count DESC, avg_gpa DESC NULLS LAST
        """,
    },
    {
        "label": "Interviewer workload",
        "keywords": ("interviewer", "workload", "assigned", "feedback pending"),
        "sql": """
            SELECT
                i.full_name,
                i.specialization,
                COUNT(s.schedule_id) AS assigned_interviews,
                COUNT(f.feedback_id) AS completed_feedback,
                COUNT(s.schedule_id) - COUNT(f.feedback_id) AS pending_feedback
            FROM interviewers i
            LEFT JOIN interview_schedules s ON s.interviewer_id = i.interviewer_id
            LEFT JOIN interview_feedback f ON f.schedule_id = s.schedule_id
            GROUP BY i.interviewer_id, i.full_name, i.specialization
            ORDER BY pending_feedback DESC, assigned_interviews DESC
        """,
    },
    {
        "label": "Profile changes",
        "keywords": ("audit", "changes", "profile changes", "changed"),
        "sql": """
            SELECT
                c.first_name,
                c.last_name,
                a.field_changed,
                a.old_value,
                a.new_value,
                a.changed_at
            FROM candidate_audit_log a
            JOIN candidates c ON c.candidate_id = a.candidate_id
            ORDER BY a.changed_at DESC
            LIMIT 30
        """,
    },
    {
        "label": "ML feature insights",
        "keywords": ("ml", "model", "feature", "importance", "predict"),
        "sql": """
            SELECT model_name, feature_rank, feature, importance
            FROM analytics.ml_feature_insights
            ORDER BY model_name, feature_rank
            LIMIT 45
        """,
    },
]


def schema_markdown():
    return "\n".join(f"- `{name}`: {description}" for name, description in SCHEMA_GUIDE.items())


def build_assistant_sql(question):
    """Return a read-only SQL statement for a natural-language question or SQL input."""
    question = (question or "").strip()
    if not question:
        return None, "Ask a question or paste a read-only SQL query."

    if looks_like_sql(question):
        return sanitize_read_only_sql(question), "Custom SQL"

    normalized = re.sub(r"\s+", " ", question.lower())
    scored_patterns = []
    for pattern in QUESTION_PATTERNS:
        score = sum(1 for keyword in pattern["keywords"] if keyword in normalized)
        if score:
            scored_patterns.append((score, pattern))

    if scored_patterns:
        scored_patterns.sort(key=lambda item: item[0], reverse=True)
        pattern = scored_patterns[0][1]
        return sanitize_read_only_sql(pattern["sql"]), pattern["label"]

    return None, (
        "I could not confidently translate that yet. Try one of the suggested questions, "
        "or paste a SELECT/WITH query using the listed tables."
    )


def looks_like_sql(text):
    lowered = text.lstrip().lower()
    return re.match(r"^(select|with)\b", lowered) is not None


def sanitize_read_only_sql(sql):
    cleaned = sql.strip().rstrip(";")
    lowered = cleaned.lower()
    tokens = set(re.findall(r"[a-z_]+", lowered))

    if ";" in cleaned:
        raise ValueError("Only one read-only query can be run at a time.")
    if BLOCKED_SQL_WORDS.intersection(tokens):
        raise ValueError("Only SELECT/WITH queries are allowed in the assistant.")
    if not looks_like_sql(cleaned):
        raise ValueError("The assistant can only run SELECT/WITH queries.")
    if SENSITIVE_COLUMNS.intersection(tokens):
        raise ValueError("Password fields are blocked from assistant results.")

    if not re.search(r"\blimit\s+\d+\b", lowered):
        cleaned = f"SELECT * FROM (\n{cleaned}\n) AS talentflow_agent_result\nLIMIT 100"

    return cleaned
