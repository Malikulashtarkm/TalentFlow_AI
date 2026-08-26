from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from analytics_assistant import build_assistant_sql
from genai_hiring_copilot import (
    build_copilot_pack,
    generate_interview_kit,
    generate_job_description,
    generate_outreach_message,
    redact_sensitive_text,
    summarize_feedback,
)


@dataclass
class AgentMessage:
    agent_name: str
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRun:
    run_type: str
    final_answer: str
    artifacts: dict[str, Any]
    trace: list[AgentMessage]
    guardrail_score: int
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


ROUTE_KEYWORDS = {
    "recruiter": {"outreach", "email", "message", "job description", "jd", "role"},
    "interview": {"interview", "question", "rubric", "assessment", "round"},
    "analytics": {"sql", "data", "dashboard", "kpi", "metric", "pipeline", "hire rate", "summary"},
    "risk": {"bias", "pii", "privacy", "guardrail", "safe", "compliance"},
}


def run_genai_agent_team(prompt, candidate=None, job=None, stage_name="Technical", feedback_rows=None):
    safe_prompt = redact_sensitive_text(prompt)
    route = route_prompt(safe_prompt)
    trace = [
        AgentMessage(
            "orchestrator",
            "planner",
            f"Routed request to {', '.join(route)} agent(s).",
            {"route": route, "redacted_prompt": safe_prompt},
        )
    ]
    artifacts = {}

    if "recruiter" in route:
        artifacts["job_description"] = generate_job_description(job or {})
        artifacts["candidate_outreach"] = generate_outreach_message(candidate or {}, job or {})
        trace.append(
            AgentMessage(
                "recruiter_agent",
                "generator",
                "Prepared recruiter-facing job and outreach drafts from structured context.",
            )
        )

    if "interview" in route:
        artifacts["interview_kit"] = generate_interview_kit(job or {}, stage_name, candidate or {})
        artifacts["feedback_summary"] = summarize_feedback(feedback_rows or [])
        trace.append(
            AgentMessage(
                "interview_agent",
                "generator",
                "Created interview questions, rubrics, and feedback summary with role context.",
            )
        )

    if "analytics" in route:
        sql, label = build_assistant_sql(safe_prompt)
        artifacts["analytics_plan"] = {
            "title": label,
            "sql": sql,
            "requires_execution": sql is not None,
        }
        trace.append(
            AgentMessage(
                "analytics_agent",
                "tool_planner",
                "Mapped the request to a guarded read-only analytics plan.",
                {"title": label, "has_sql": sql is not None},
            )
        )

    risk_report = evaluate_guardrails(safe_prompt, artifacts)
    artifacts["risk_report"] = risk_report
    trace.append(
        AgentMessage(
            "risk_agent",
            "reviewer",
            risk_report["summary"],
            {"score": risk_report["score"], "findings": risk_report["findings"]},
        )
    )

    final_answer = compose_final_answer(route, artifacts, risk_report)
    return AgentRun(
        run_type="multi_agent_genai_workflow",
        final_answer=final_answer,
        artifacts=artifacts,
        trace=trace,
        guardrail_score=risk_report["score"],
    )


def route_prompt(prompt):
    normalized = (prompt or "").lower()
    route = []
    for agent_name, keywords in ROUTE_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            route.append(agent_name)
    if not route:
        route = ["recruiter", "interview", "analytics"]
    if "risk" not in route:
        route.append("risk")
    return route


def evaluate_guardrails(prompt, artifacts):
    findings = []
    combined = f"{prompt}\n{artifacts}".lower()

    if "[email]" in combined or "[phone]" in combined:
        findings.append("Sensitive contact details were redacted before generation.")
    if any(term in combined for term in ["age", "gender", "married", "religion", "caste"]):
        findings.append("Potential protected-attribute language needs human review.")
    if "analytics_plan" in artifacts and not artifacts["analytics_plan"].get("sql"):
        findings.append("Analytics request was not executed because no safe SQL plan was found.")
    if "password" in combined:
        findings.append("Blocked field detected in context; remove it before using model output.")

    score = 100
    score -= 20 * sum("protected-attribute" in finding for finding in findings)
    score -= 25 * sum("Blocked field" in finding for finding in findings)
    score -= 10 * sum("no safe SQL" in finding for finding in findings)
    score = max(score, 0)

    if not findings:
        findings.append("No obvious PII, unsafe SQL, or protected-attribute issue detected.")

    return {
        "score": score,
        "findings": findings,
        "summary": f"Guardrail review completed with score {score}/100.",
    }


def compose_final_answer(route, artifacts, risk_report):
    lines = [
        "Multi-agent run complete.",
        f"Agents used: {', '.join(route)}.",
        risk_report["summary"],
    ]
    if artifacts.get("analytics_plan", {}).get("requires_execution"):
        lines.append("Analytics agent produced a safe SQL plan ready for execution in Ask Data.")
    if "job_description" in artifacts:
        lines.append("Recruiter agent produced a job description and outreach draft.")
    if "interview_kit" in artifacts:
        lines.append("Interview agent produced questions, rubrics, and feedback summary.")
    lines.append("Use outputs as drafts; final hiring decisions stay human-owned.")
    return "\n".join(lines)


def serialize_agent_run(run):
    return {
        "run_type": run.run_type,
        "final_answer": run.final_answer,
        "artifacts": run.artifacts,
        "trace": [
            {
                "agent_name": item.agent_name,
                "role": item.role,
                "content": item.content,
                "metadata": item.metadata,
            }
            for item in run.trace
        ],
        "guardrail_score": run.guardrail_score,
        "created_at": run.created_at,
    }


def build_full_hiring_pack(candidate, job, stage_name, feedback_rows=None):
    pack = build_copilot_pack(candidate, job, stage_name, feedback_rows)
    run = run_genai_agent_team(
        "Create recruiter outreach, an interview kit, a feedback summary, and risk review.",
        candidate=candidate,
        job=job,
        stage_name=stage_name,
        feedback_rows=feedback_rows,
    )
    pack["agent_trace"] = serialize_agent_run(run)["trace"]
    pack["risk_report"] = run.artifacts["risk_report"]
    return pack
