import json
import os
import re
from functools import lru_cache

from analytics_assistant import sanitize_read_only_sql

try:
    from langchain_core.prompts import PromptTemplate
except ModuleNotFoundError:
    PromptTemplate = None


DEFAULT_HF_MODEL = os.environ.get("LOCAL_HF_MODEL", "Qwen/Qwen2.5-Coder-1.5B-Instruct")


SQL_PLAN_PROMPT_TEMPLATE = """
You are TalentFlow AI's local text-to-SQL agent.

Task:
Generate one PostgreSQL SELECT query for the user's recruitment analytics question.

Rules:
- Use only tables and columns from the schema.
- Never select password or secret fields.
- Never write INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, COPY, GRANT, or REVOKE.
- Prefer aggregates and joins for business questions.
- Add LIMIT unless the query returns one aggregate row.
- Return only JSON, with no markdown.

JSON shape:
{{"title":"short answer title","sql":"SELECT ...","chart_type":"auto|metric|bar|line|table","reasoning":"one sentence"}}

Schema:
{schema_context}

Learned examples:
{learned_examples}

User question:
{question}
""".strip()


SQL_REPAIR_PROMPT_TEMPLATE = """
You are TalentFlow AI's local text-to-SQL repair agent.

The previous PostgreSQL SELECT query failed. Generate a corrected safe read-only query.

Rules:
- Use only the provided schema.
- Never select password or secret fields.
- Never write mutating SQL.
- Return only JSON, with no markdown.

JSON shape:
{{"title":"short answer title","sql":"SELECT ...","chart_type":"auto|metric|bar|line|table","reasoning":"one sentence"}}

Schema:
{schema_context}

Learned examples:
{learned_examples}

User question:
{question}

Failed SQL:
{previous_sql}

Database error:
{error_message}
""".strip()


def huggingface_enabled():
    provider = os.environ.get("LOCAL_LLM_PROVIDER", "").lower()
    return provider in {"hf", "huggingface", "transformers"}


def generate_huggingface_sql_plan(question, schema_context, examples=None):
    prompt = _build_prompt(question, schema_context, examples or [])
    raw_output = _generate_text(prompt)
    plan = _parse_plan(raw_output)
    plan["sql"] = sanitize_read_only_sql(plan["sql"])
    plan["mode"] = "LangChain + Hugging Face local LLM"
    return plan


def repair_huggingface_sql(question, schema_context, previous_sql, error_message, examples=None):
    prompt = _build_repair_prompt(question, schema_context, previous_sql, error_message, examples or [])
    raw_output = _generate_text(prompt)
    plan = _parse_plan(raw_output)
    plan["sql"] = sanitize_read_only_sql(plan["sql"])
    plan["mode"] = "LangChain + Hugging Face local LLM repair"
    return plan


@lru_cache(maxsize=1)
def _load_pipeline():
    try:
        from transformers import pipeline
        import torch  # noqa: F401
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Hugging Face local LLM mode needs transformers and torch. "
            "Start the app with .\\.venv\\Scripts\\python.exe -m streamlit run app\\portal.py "
            "or install them with .\\.venv\\Scripts\\python.exe -m pip install transformers torch accelerate"
        ) from exc

    model_name = os.environ.get("LOCAL_HF_MODEL", DEFAULT_HF_MODEL)
    device = os.environ.get("LOCAL_HF_DEVICE", "-1")
    device_arg = int(device) if device.lstrip("-").isdigit() else device
    return pipeline(
        "text-generation",
        model=model_name,
        device=device_arg,
        trust_remote_code=False,
    )


def _generate_text(prompt):
    pipe = _load_pipeline()
    max_new_tokens = int(os.environ.get("LOCAL_HF_MAX_NEW_TOKENS", "600"))
    output = pipe(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        return_full_text=False,
    )
    if not output:
        raise ValueError("The local Hugging Face model returned no output.")
    return output[0].get("generated_text", "")


def _build_prompt(question, schema_context, examples):
    learned_examples = _format_examples(examples)
    return _format_prompt(
        SQL_PLAN_PROMPT_TEMPLATE,
        question=question,
        schema_context=schema_context,
        learned_examples=learned_examples,
    )


def _build_repair_prompt(question, schema_context, previous_sql, error_message, examples):
    learned_examples = _format_examples(examples)
    return _format_prompt(
        SQL_REPAIR_PROMPT_TEMPLATE,
        question=question,
        schema_context=schema_context,
        learned_examples=learned_examples,
        previous_sql=previous_sql,
        error_message=error_message,
    )


def _format_prompt(template, **values):
    if PromptTemplate is None:
        return template.format(**values)

    return PromptTemplate.from_template(template, template_format="f-string").format(**values)


def _format_examples(examples):
    if not examples:
        return "None"
    formatted = []
    for row in examples[:5]:
        sql = row.get("corrected_sql") or row.get("generated_sql")
        if not sql:
            continue
        formatted.append(
            json.dumps(
                {
                    "question": row.get("question"),
                    "sql": sql,
                    "chart_type": row.get("chart_type") or "auto",
                },
                default=str,
            )
        )
    return "\n".join(formatted) if formatted else "None"


def _parse_plan(raw_output):
    text = (raw_output or "").strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            return {
                "title": str(parsed.get("title") or "Local LLM answer"),
                "sql": str(parsed["sql"]),
                "chart_type": str(parsed.get("chart_type") or "auto").lower(),
                "reasoning": str(parsed.get("reasoning") or "Generated by the local Hugging Face model."),
            }
        except (KeyError, json.JSONDecodeError):
            pass

    sql_match = re.search(r"```sql\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    sql = sql_match.group(1).strip() if sql_match else text
    sql = re.sub(r"^sql\s*:", "", sql, flags=re.IGNORECASE).strip()
    return {
        "title": "Local LLM answer",
        "sql": sql,
        "chart_type": "auto",
        "reasoning": "Generated by the local Hugging Face model.",
    }
