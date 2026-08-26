import json
import os
import re
import urllib.error
import urllib.request
from datetime import date, datetime
from decimal import Decimal

from analytics_assistant import sanitize_read_only_sql
from huggingface_sql_agent import generate_huggingface_sql_plan, huggingface_enabled, repair_huggingface_sql
from local_sql_model import generate_local_sql_plan


DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.2")
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
MAX_RESULT_ROWS_FOR_MEMORY = 1000
TRUTHY_ENV_VALUES = {"1", "true", "yes"}


def ensure_agent_tables(cur):
    cur.execute("CREATE SCHEMA IF NOT EXISTS analytics")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analytics.agent_interactions (
            interaction_id SERIAL PRIMARY KEY,
            user_email TEXT,
            question TEXT NOT NULL,
            generated_sql TEXT,
            answer_summary TEXT,
            chart_type TEXT,
            row_count INTEGER DEFAULT 0,
            was_helpful BOOLEAN,
            corrected_sql TEXT,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_agent_interactions_feedback
        ON analytics.agent_interactions (was_helpful, created_at DESC)
        """
    )


def get_schema_context(cur):
    cur.execute(
        """
        SELECT table_schema, table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema IN ('public', 'analytics')
          AND column_name <> 'password'
        ORDER BY table_schema, table_name, ordinal_position
        """
    )
    rows = cur.fetchall()
    grouped = {}
    for row in rows:
        table = f"{row['table_schema']}.{row['table_name']}"
        grouped.setdefault(table, []).append(f"{row['column_name']} {row['data_type']}")

    lines = []
    for table, columns in grouped.items():
        lines.append(f"{table}: {', '.join(columns)}")
    return "\n".join(lines)


def retrieve_agent_examples(cur, question, limit=5):
    ensure_agent_tables(cur)
    cur.execute(
        """
        SELECT question, generated_sql, corrected_sql, answer_summary, chart_type, was_helpful
        FROM analytics.agent_interactions
        WHERE generated_sql IS NOT NULL
          AND (was_helpful IS TRUE OR corrected_sql IS NOT NULL)
        ORDER BY created_at DESC
        LIMIT 40
        """
    )
    rows = cur.fetchall()
    question_terms = _terms(question)
    scored = []
    for row in rows:
        score = len(question_terms.intersection(_terms(row["question"])))
        if score:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[:limit]]


def generate_agent_plan(cur, question, user_email=None):
    examples = retrieve_agent_examples(cur, question)
    api_key = os.environ.get("OPENAI_API_KEY")
    local_only = _env_enabled("LOCAL_AGENT_ONLY")
    speed_mode = os.environ.get("LOCAL_AGENT_SPEED_MODE", "fast").lower()
    allow_slow_llm = _env_enabled("LOCAL_ALLOW_SLOW_LLM")
    local_first_confidence = float(os.environ.get("LOCAL_FIRST_CONFIDENCE", "0.10"))

    if huggingface_enabled():
        if speed_mode != "llm_first":
            try:
                plan = generate_local_sql_plan(question, examples, min_confidence=local_first_confidence)
                plan["mode"] = "Fast local SQL agent"
                plan["reasoning"] = (
                    f"{plan.get('reasoning', '').rstrip()} Hugging Face was skipped so the answer stays fast."
                )
                return plan
            except Exception as local_exc:
                if not allow_slow_llm:
                    raise ValueError(
                        "The fast local agent could not confidently map this question. "
                        "Rephrase it, paste read-only SQL, or set LOCAL_ALLOW_SLOW_LLM=true if you want to allow slower Hugging Face generation."
                    ) from local_exc

        try:
            schema_context = get_schema_context(cur)
            return generate_huggingface_sql_plan(question, schema_context, examples)
        except Exception as exc:
            plan = generate_local_sql_plan(question, examples)
            plan["mode"] = "Local semantic fallback"
            plan["reasoning"] = (
                "The Hugging Face local LLM could not answer, so the local semantic model answered instead. "
                f"Local LLM error: {exc}"
            )
            return plan

    if local_only:
        return generate_local_sql_plan(question, examples)

    if api_key:
        try:
            schema_context = get_schema_context(cur)
            plan = _generate_llm_plan(api_key, question, schema_context, examples, user_email)
            plan["sql"] = sanitize_read_only_sql(plan["sql"])
            plan["mode"] = "AI agent"
            return plan
        except Exception as exc:
            plan = generate_local_sql_plan(question, examples)
            plan["mode"] = "Local model fallback"
            plan["reasoning"] = (
                "The cloud AI call failed, so the free local model answered from built-in and learned examples. "
                f"Cloud error: {exc}"
            )
            return plan

    return generate_local_sql_plan(question, examples)


def generate_result_narrative(question, sql, rows, plan):
    if not rows:
        return "I ran the query successfully, but it returned no matching rows."

    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key and _env_enabled("OPENAI_RESULT_NARRATIVE"):
        try:
            sample_rows = [_json_safe(dict(row)) for row in rows[:15]]
            payload = {
                "question": question,
                "sql": sql,
                "row_count": len(rows),
                "sample_rows": sample_rows,
            }
            text = _call_openai_json(
                api_key,
                [
                    {
                        "role": "system",
                        "content": (
                            "You explain recruitment analytics results for a TalentFlow AI admin. "
                            "Be concise. Mention the direct answer, important pattern, and one suggested next action. "
                            "Do not invent values that are not present in the rows."
                        ),
                    },
                    {"role": "user", "content": json.dumps(payload, default=str)},
                ],
                json_mode=False,
                max_output_tokens=350,
            )
            if text:
                return text.strip()
        except Exception:
            pass

    return _fallback_narrative(rows, plan)


def repair_agent_plan(cur, question, previous_plan, error_message):
    if not huggingface_enabled():
        raise ValueError("Automatic SQL repair is available in Hugging Face local LLM mode.")

    schema_context = get_schema_context(cur)
    examples = retrieve_agent_examples(cur, question)
    return repair_huggingface_sql(
        question,
        schema_context,
        previous_plan.get("sql", ""),
        error_message,
        examples,
    )


def record_agent_interaction(cur, user_email, question, plan, summary, row_count, error_message=None):
    ensure_agent_tables(cur)
    cur.execute(
        """
        INSERT INTO analytics.agent_interactions
            (user_email, question, generated_sql, answer_summary, chart_type, row_count, error_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING interaction_id
        """,
        (
            user_email,
            question,
            plan.get("sql"),
            summary,
            plan.get("chart_type"),
            min(row_count or 0, MAX_RESULT_ROWS_FOR_MEMORY),
            error_message,
        ),
    )
    return cur.fetchone()["interaction_id"]


def update_agent_feedback(cur, interaction_id, was_helpful, corrected_sql=None):
    corrected_sql = corrected_sql.strip() if corrected_sql else None
    if corrected_sql:
        corrected_sql = sanitize_read_only_sql(corrected_sql)
    cur.execute(
        """
        UPDATE analytics.agent_interactions
        SET was_helpful = %s, corrected_sql = COALESCE(%s, corrected_sql)
        WHERE interaction_id = %s
        """,
        (was_helpful, corrected_sql, interaction_id),
    )


def _generate_llm_plan(api_key, question, schema_context, examples, user_email):
    example_context = [
        {
            "question": row["question"],
            "sql": row["corrected_sql"] or row["generated_sql"],
            "chart_type": row["chart_type"] or "auto",
        }
        for row in examples
    ]
    prompt = {
        "user_email": user_email,
        "question": question,
        "database_schema": schema_context,
        "learned_examples": example_context,
        "allowed_chart_types": ["auto", "metric", "bar", "line", "table"],
    }
    content = _call_openai_json(
        api_key,
        [
            {
                "role": "system",
                "content": (
                    "You are TalentFlow AI's analytics SQL agent. Generate one PostgreSQL read-only query "
                    "for the user's recruitment analytics question. Use only tables and columns from the schema. "
                    "Never select password or secret fields. Prefer aggregates for business questions. "
                    "Return strict JSON with keys: title, sql, chart_type, reasoning. "
                    "chart_type must be one of auto, metric, bar, line, table."
                ),
            },
            {"role": "user", "content": json.dumps(prompt)},
        ],
        json_mode=True,
        max_output_tokens=900,
    )
    plan = json.loads(content)
    if "sql" not in plan:
        raise ValueError("The AI response did not include SQL.")
    return {
        "title": str(plan.get("title") or "AI-generated answer"),
        "sql": str(plan["sql"]),
        "chart_type": str(plan.get("chart_type") or "auto").lower(),
        "reasoning": str(plan.get("reasoning") or ""),
    }


def _call_openai_json(api_key, messages, json_mode, max_output_tokens):
    body = {
        "model": DEFAULT_MODEL,
        "input": messages,
        "max_output_tokens": max_output_tokens,
    }
    if json_mode:
        body["text"] = {
            "format": {
                "type": "json_schema",
                "name": "talentflow_sql_plan",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "sql": {"type": "string"},
                        "chart_type": {
                            "type": "string",
                            "enum": ["auto", "metric", "bar", "line", "table"],
                        },
                        "reasoning": {"type": "string"},
                    },
                    "required": ["title", "sql", "chart_type", "reasoning"],
                },
            }
        }

    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI API request failed: {detail}") from exc

    text = _extract_response_text(payload)
    if not text:
        raise ValueError("OpenAI API returned no text output.")
    return text


def _extract_response_text(payload):
    if payload.get("output_text"):
        return payload["output_text"]

    parts = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if "text" in content:
                parts.append(content["text"])
    return "\n".join(parts)


def _fallback_narrative(rows, plan):
    title = plan.get("title", "answer")
    row_count = len(rows)
    first_row = dict(rows[0])
    numeric_items = [
        (key, value)
        for key, value in first_row.items()
        if isinstance(value, (int, float, Decimal)) and value is not None
    ]
    if row_count == 1 and numeric_items:
        highlights = ", ".join(f"{key.replace('_', ' ')} = {value}" for key, value in numeric_items[:4])
        return f"{title}: {highlights}."
    return f"{title}: I found {row_count} matching rows. The table and chart below show the main pattern."


def _terms(text):
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", (text or "").lower())
        if len(token) > 2
        and token not in {"the", "and", "for", "with", "show", "give", "what", "which"}
    }


def _env_enabled(name):
    return os.environ.get(name, "").lower() in TRUTHY_ENV_VALUES


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


