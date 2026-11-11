# GenAI Engineer Interview Prep For TalentFlow AI

## 60-second project pitch

TalentFlow AI is an end-to-end recruitment intelligence platform. It starts with a Streamlit portal for candidates, interviewers, and admins, stores operational data in PostgreSQL, moves it through bronze, silver, and gold lakehouse layers, protects PII in the silver layer, publishes analytics KPIs, trains ML feature-importance insights, and exposes GenAI features for both analytics and recruiting workflows.

The GenAI layer has two parts:

- A conversational analytics agent that translates hiring questions into safe read-only SQL, executes the query, narrates the result, recommends a chart type, and learns from admin feedback.
- A multi-agent hiring studio that uses recruiter, interview, analytics, and risk agents to generate job descriptions, outreach drafts, interview kits, analytics plans, feedback summaries, traces, and guardrail scores from redacted project data.

## GenAI aspects to highlight

- Text-to-SQL: schema-aware prompt context, generated SQL validation, read-only enforcement, sensitive-column blocking, row limits, and one repair path for local LLM mode.
- RAG-style grounding: the agent retrieves schema and previously corrected examples before answering.
- Local-first fallback: a deterministic semantic SQL model answers known questions without cloud cost, while Hugging Face or OpenAI can be enabled through environment variables.
- Human feedback loop: useful answers and corrected SQL are stored in `analytics.agent_interactions` and reused as examples.
- Agent orchestration: `app/genai_agent_orchestrator.py` routes requests, records agent messages, stores traces, and composes the final answer.
- Responsible AI: PII redaction, password/email/phone exclusion, human review notes, and no fully automated hiring decision.
- LLMOps readiness: model/provider configuration is externalized, generated outputs are auditable, agent traces are stored, and tests cover safety contracts.

## Questions you should be ready for

1. How do you prevent unsafe SQL?
Answer: I only allow `SELECT` or `WITH`, block mutation keywords, reject multiple statements, block sensitive fields like passwords, and automatically wrap queries with a limit when needed.

2. What happens if the LLM is wrong?
Answer: The system validates the query before execution, catches SQL failures, attempts a repair in local LLM mode, and lets admins submit corrected SQL that becomes future retrieval context.

3. Why use GenAI here instead of normal dashboards?
Answer: Dashboards answer predefined questions. GenAI lets recruiters ask new questions in natural language and generate workflow artifacts like interview kits and outreach while still grounding the output in trusted data.

4. How do you handle privacy?
Answer: PII is removed from prompt context where possible, password fields are excluded from schema and outputs, and generated recruiting artifacts are positioned as drafts requiring human review.

5. What would you improve next?
Answer: I would add embeddings for stronger example retrieval, structured evaluation datasets for text-to-SQL accuracy, model latency/cost tracking, prompt versioning, and role-based access control.

## Demo path

1. Register or open a candidate profile.
2. Schedule an interview as admin.
3. Submit interviewer feedback.
4. Run the ELT pipeline and show gold KPIs.
5. Open Ask Data and ask: "Which candidates have high ratings but were not hired?"
6. Open GenAI Copilot and generate a role-specific pack.
7. Explain the guardrails: redacted context, stored output audit, and human review.
