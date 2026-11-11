import math
import re
from collections import Counter

from analytics_assistant import QUESTION_PATTERNS, build_assistant_sql, looks_like_sql, sanitize_read_only_sql


LOCAL_SQL_USE_CASES = [
    {
        "title": "Interviewer assignments",
        "questions": [
            "Who is the interviewer interviewing?",
            "Which candidate is each interviewer interviewing?",
            "Show interviewer candidate assignments",
            "Who are interviewers assigned to interview?",
            "List interviewers and their candidates",
        ],
        "chart_type": "table",
        "sql": """
            SELECT
                i.full_name AS interviewer,
                c.first_name || ' ' || c.last_name AS candidate,
                j.job_title,
                st.stage_name,
                s.interview_date,
                s.status
            FROM interview_schedules s
            JOIN interviewers i ON i.interviewer_id = s.interviewer_id
            JOIN candidates c ON c.candidate_id = s.candidate_id
            JOIN jobs j ON j.job_id = s.job_id
            JOIN interview_stages st ON st.stage_id = s.stage_id
            ORDER BY s.interview_date DESC NULLS LAST, interviewer, candidate
            LIMIT 50
        """,
    },
    {
        "title": "High-rated candidates not hired",
        "questions": [
            "Which candidates have high ratings but were not hired?",
            "Show strong candidates who did not get a hire decision",
            "Candidates with good interview feedback but hold or reject decision",
        ],
        "chart_type": "bar",
        "sql": """
            SELECT
                c.first_name,
                c.last_name,
                c.city,
                j.job_title,
                ROUND(AVG(f.rating)::numeric, 2) AS avg_rating,
                STRING_AGG(DISTINCT f.decision, ', ') AS decisions,
                COUNT(f.feedback_id) AS feedback_count
            FROM candidates c
            JOIN interview_schedules s ON s.candidate_id = c.candidate_id
            JOIN jobs j ON j.job_id = s.job_id
            JOIN interview_feedback f ON f.schedule_id = s.schedule_id
            GROUP BY c.candidate_id, c.first_name, c.last_name, c.city, j.job_title
            HAVING AVG(f.rating) >= 4
               AND COUNT(*) FILTER (WHERE LOWER(f.decision) = 'hire') = 0
            ORDER BY avg_rating DESC, feedback_count DESC
            LIMIT 25
        """,
    },
    {
        "title": "City pipeline strength",
        "questions": [
            "Which cities have the strongest candidate pipeline?",
            "Best city for talent pipeline",
            "Compare candidates interviews and hires by city",
        ],
        "chart_type": "bar",
        "sql": """
            SELECT
                c.city,
                COUNT(DISTINCT c.candidate_id) AS candidate_count,
                COUNT(DISTINCT s.schedule_id) AS interview_count,
                COUNT(*) FILTER (WHERE LOWER(f.decision) = 'hire') AS hire_recommendations,
                ROUND(AVG(f.rating)::numeric, 2) AS avg_rating
            FROM candidates c
            LEFT JOIN interview_schedules s ON s.candidate_id = c.candidate_id
            LEFT JOIN interview_feedback f ON f.schedule_id = s.schedule_id
            GROUP BY c.city
            ORDER BY hire_recommendations DESC, avg_rating DESC NULLS LAST, candidate_count DESC
            LIMIT 20
        """,
    },
    {
        "title": "Degrees associated with better ratings",
        "questions": [
            "Which degrees are associated with better ratings?",
            "Compare education degree with interview performance",
            "Best performing degrees by average rating",
        ],
        "chart_type": "bar",
        "sql": """
            SELECT
                e.degree,
                COUNT(DISTINCT c.candidate_id) AS candidate_count,
                COUNT(f.feedback_id) AS feedback_count,
                ROUND(AVG(e.gpa)::numeric, 2) AS avg_gpa,
                ROUND(AVG(f.rating)::numeric, 2) AS avg_rating
            FROM candidate_education e
            JOIN candidates c ON c.candidate_id = e.candidate_id
            LEFT JOIN interview_schedules s ON s.candidate_id = c.candidate_id
            LEFT JOIN interview_feedback f ON f.schedule_id = s.schedule_id
            GROUP BY e.degree
            HAVING COUNT(f.feedback_id) > 0
            ORDER BY avg_rating DESC NULLS LAST, feedback_count DESC
            LIMIT 20
        """,
    },
    {
        "title": "Inactive candidates",
        "questions": [
            "Which active candidates have not logged in recently?",
            "Candidates with no recent login",
            "Show candidates who are inactive for 30 days",
        ],
        "chart_type": "bar",
        "sql": """
            SELECT
                c.first_name,
                c.last_name,
                c.email,
                c.city,
                COUNT(l.log_id) AS login_count,
                MAX(l.login_timestamp) AS latest_login
            FROM candidates c
            LEFT JOIN login_logs l ON l.candidate_id = c.candidate_id
            GROUP BY c.candidate_id, c.first_name, c.last_name, c.email, c.city
            HAVING MAX(l.login_timestamp) IS NULL
                OR MAX(l.login_timestamp) < NOW() - INTERVAL '30 days'
            ORDER BY latest_login ASC NULLS FIRST, login_count ASC
            LIMIT 30
        """,
    },
    {
        "title": "Pipeline bottlenecks",
        "questions": [
            "Where is the hiring pipeline stuck?",
            "Show bottlenecks by stage and status",
            "Which interview stages have most pending candidates?",
        ],
        "chart_type": "bar",
        "sql": """
            SELECT
                st.stage_name,
                s.status,
                COUNT(s.schedule_id) AS interview_count
            FROM interview_schedules s
            JOIN interview_stages st ON st.stage_id = s.stage_id
            GROUP BY st.stage_name, s.status
            ORDER BY interview_count DESC, st.stage_name, s.status
            LIMIT 30
        """,
    },
    {
        "title": "Question bank coverage",
        "questions": [
            "Do we have enough interview questions by role?",
            "Show question bank coverage by job title and category",
            "Question coverage for each role",
        ],
        "chart_type": "bar",
        "sql": """
            SELECT
                job_title,
                category,
                COUNT(question_id) AS question_count
            FROM questions_bank
            GROUP BY job_title, category
            ORDER BY question_count DESC, job_title, category
            LIMIT 40
        """,
    },
]


def generate_local_sql_plan(question, learned_examples=None, min_confidence=0.12):
    if looks_like_sql(question or ""):
        direct_sql, direct_label = build_assistant_sql(question)
        return {
            "mode": "Local model",
            "title": direct_label,
            "sql": direct_sql,
            "chart_type": "auto",
            "reasoning": "The local model matched this to a safe built-in query.",
            "confidence": 1.0,
        }

    candidates = _training_examples(learned_examples or [])
    best = _best_match(question, candidates)
    if best and best["score"] >= min_confidence:
        sql = sanitize_read_only_sql(best["sql"])
        return {
            "mode": "Local model",
            "title": best["title"],
            "sql": sql,
            "chart_type": best["chart_type"],
            "reasoning": (
                f"The free local model matched this request to a learned use case "
                f"with {best['score']:.0%} similarity."
            ),
            "confidence": best["score"],
        }

    direct_sql, direct_label = build_assistant_sql(question)
    if direct_sql:
        return {
            "mode": "Local model",
            "title": direct_label,
            "sql": direct_sql,
            "chart_type": "auto",
            "reasoning": "The local model matched this to a safe built-in query.",
            "confidence": 1.0,
        }

    if not best or best["score"] < min_confidence:
        raise ValueError(
            "The free local model has not learned this question yet. Try rephrasing, use one of the examples, "
            "or paste a read-only SQL query. If you provide corrected SQL through Teach the Agent, it can reuse it later."
        )


def _training_examples(learned_examples):
    examples = []
    for pattern in QUESTION_PATTERNS:
        label = pattern["label"]
        sql = pattern["sql"]
        examples.append(
            {
                "title": label,
                "text": f"{label} {' '.join(pattern['keywords'])}",
                "sql": sql,
                "chart_type": "auto",
            }
        )

    for use_case in LOCAL_SQL_USE_CASES:
        for question in use_case["questions"]:
            examples.append(
                {
                    "title": use_case["title"],
                    "text": question,
                    "sql": use_case["sql"],
                    "chart_type": use_case["chart_type"],
                }
            )

    for row in learned_examples:
        sql = row.get("corrected_sql") or row.get("generated_sql")
        if not sql:
            continue
        examples.append(
            {
                "title": "Learned answer",
                "text": row.get("question") or "",
                "sql": sql,
                "chart_type": row.get("chart_type") or "auto",
            }
        )

    return examples


def _best_match(question, candidates):
    query_terms = _weighted_terms(question)
    if not query_terms:
        return None

    documents = [_weighted_terms(candidate["text"]) for candidate in candidates]
    doc_freq = Counter()
    for document in documents:
        doc_freq.update(document.keys())

    scored = []
    for candidate, document in zip(candidates, documents):
        score = _tfidf_cosine(query_terms, document, doc_freq, len(documents))
        scored.append({**candidate, "score": score})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[0] if scored else None


def _tfidf_cosine(left, right, doc_freq, doc_count):
    shared_terms = set(left).intersection(right)
    if not shared_terms:
        return 0.0

    def weight(term, counts):
        idf = math.log((doc_count + 1) / (doc_freq[term] + 1)) + 1
        return counts[term] * idf

    numerator = sum(weight(term, left) * weight(term, right) for term in shared_terms)
    left_norm = math.sqrt(sum(weight(term, left) ** 2 for term in left))
    right_norm = math.sqrt(sum(weight(term, right) ** 2 for term in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def _weighted_terms(text):
    tokens = [
        token
        for token in re.findall(r"[a-z0-9_]+", (text or "").lower())
        if len(token) > 2
        and token not in {
            "the",
            "and",
            "for",
            "with",
            "show",
            "give",
            "what",
            "which",
            "have",
            "has",
            "are",
            "was",
            "were",
            "from",
            "that",
            "this",
        }
    ]
    return Counter(tokens)
