from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from build_wilp_final_report import (
    ABSTRACT,
    BITS_ID,
    COURSE,
    EXAMINER,
    ORG,
    PROGRAM,
    REFERENCES,
    STUDENT,
    SUBTITLE,
    SUPERVISOR,
    TITLE,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "TalentFlow_AI_Final_Project_Report_2024DA04133.pdf"
PAGE_SIZE = (9 * inch, 11 * inch)
BODY_START_PHYSICAL_PAGE = 6
TOC_PAGE_NUMBERS = {}
TOC_ENTRIES = [
    "1. Introduction",
    "2. Literature and Technology Background",
    "3. Requirement Analysis",
    "4. System Design",
    "5. Database Design",
    "6. Implementation",
    "7. Data Engineering and Lakehouse Pipeline",
    "8. Predictive Intelligence and Analytics Agent",
    "9. Testing, Validation and Results",
    "10. Security, Privacy and Governance",
    "11. Conclusions and Recommendations",
    "12. References",
    "13. Glossary",
    "14. Appendices",
]


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle("CoverTitle", parent=base["Title"], fontSize=22, leading=27, alignment=TA_CENTER, spaceAfter=16))
    base.add(ParagraphStyle("CoverSub", parent=base["Normal"], fontSize=12, leading=16, alignment=TA_CENTER, spaceAfter=14, italic=True))
    base.add(ParagraphStyle("H1x", parent=base["Heading1"], fontSize=16, leading=20, textColor=colors.HexColor("#1F4E79"), spaceBefore=14, spaceAfter=8))
    base.add(ParagraphStyle("H2x", parent=base["Heading2"], fontSize=13, leading=16, textColor=colors.HexColor("#1F4E79"), spaceBefore=10, spaceAfter=6))
    base.add(ParagraphStyle("H3x", parent=base["Heading3"], fontSize=11.5, leading=14, textColor=colors.HexColor("#1F4D78"), spaceBefore=8, spaceAfter=4))
    base.add(ParagraphStyle("BodyJust", parent=base["BodyText"], fontName="Times-Roman", fontSize=10.5, leading=21, alignment=TA_JUSTIFY, spaceAfter=8))
    base.add(ParagraphStyle("TOCEntry", parent=base["BodyText"], fontName="Times-Roman", fontSize=10.5, leading=18, alignment=TA_LEFT, spaceAfter=2))
    base.add(ParagraphStyle("Small", parent=base["BodyText"], fontSize=8.8, leading=11, spaceAfter=3))
    base.add(ParagraphStyle("Ref", parent=base["BodyText"], fontName="Times-Roman", fontSize=9.5, leading=12.5, alignment=TA_LEFT, spaceAfter=5))
    base.add(ParagraphStyle("Caption", parent=base["BodyText"], fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), italic=True))
    return base


S = styles()


def p(text, style="BodyJust"):
    return Paragraph(text.replace("&", "&amp;"), S[style])


def h(text, level=1):
    return Paragraph(text, S["H1x" if level == 1 else "H2x" if level == 2 else "H3x"])


def tbl(headers, rows, widths=None):
    data = [[Paragraph(f"<b>{x}</b>", S["Small"]) for x in headers]]
    for row in rows:
        data.append([Paragraph(str(x).replace("&", "&amp;"), S["Small"]) for x in row])
    table = Table(data, colWidths=[w * inch for w in widths] if widths else None, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0B2545")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#BFC7D5")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [table, Spacer(1, 0.13 * inch)]


def bullet(text):
    return Paragraph("&#8226; " + text.replace("&", "&amp;"), S["BodyJust"])


def numbered(items):
    out = []
    for i, item in enumerate(items, 1):
        out.append(Paragraph(f"{i}. {item}".replace("&", "&amp;"), S["BodyJust"]))
    return out


def roman(number):
    values = [
        (1000, "m"),
        (900, "cm"),
        (500, "d"),
        (400, "cd"),
        (100, "c"),
        (90, "xc"),
        (50, "l"),
        (40, "xl"),
        (10, "x"),
        (9, "ix"),
        (5, "v"),
        (4, "iv"),
        (1, "i"),
    ]
    result = []
    for value, numeral in values:
        while number >= value:
            result.append(numeral)
            number -= value
    return "".join(result)


def footer(canvas, doc):
    page = canvas.getPageNumber()
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    if 2 <= page < BODY_START_PHYSICAL_PAGE:
        canvas.drawCentredString(PAGE_SIZE[0] / 2, 0.45 * inch, roman(page - 1))
    elif page >= BODY_START_PHYSICAL_PAGE:
        canvas.drawCentredString(PAGE_SIZE[0] / 2, 0.45 * inch, f"Page {page - BODY_START_PHYSICAL_PAGE + 1}")
        canvas.drawRightString(PAGE_SIZE[0] - inch, PAGE_SIZE[1] - 0.55 * inch, "TalentFlow AI Final Project Report")
    canvas.restoreState()


def toc_flowables():
    rows = []
    for entry in TOC_ENTRIES:
        page = TOC_PAGE_NUMBERS.get(entry, "")
        rows.append([Paragraph(entry, S["TOCEntry"]), Paragraph(str(page), S["TOCEntry"])])
    table = Table(rows, colWidths=[6.0 * inch, 0.55 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    return [table]


def build_story():
    story = []
    story += [Spacer(1, 1.0 * inch), Paragraph("<b>A REPORT</b>", S["CoverTitle"]), Paragraph("ON", S["CoverSub"]), Paragraph(f"<b>{TITLE}</b>", S["CoverTitle"]), Paragraph(SUBTITLE, S["CoverSub"])]
    story += [Spacer(1, 0.35 * inch), Paragraph("BY", S["CoverSub"]), Paragraph(f"<b>{STUDENT}<br/>ID No.: {BITS_ID}</b>", S["CoverSub"]), Spacer(1, 0.35 * inch), Paragraph("AT", S["CoverSub"]), Paragraph(f"<b>{ORG}</b>", S["CoverSub"]), Spacer(1, 1.1 * inch), Paragraph("<b>BIRLA INSTITUTE OF TECHNOLOGY &amp; SCIENCE, PILANI</b>", S["CoverSub"]), Paragraph("July 2026", S["CoverSub"]), PageBreak()]
    story += [Spacer(1, 0.4 * inch), Paragraph("<b>A REPORT</b>", S["CoverTitle"]), Paragraph("ON", S["CoverSub"]), Paragraph(f"<b>{TITLE}</b>", S["CoverTitle"]), Paragraph(SUBTITLE, S["CoverSub"]), Spacer(1, 0.25 * inch), Paragraph(f"<b>BY<br/>{STUDENT}<br/>ID No.: {BITS_ID} : {PROGRAM}</b>", S["CoverSub"]), Paragraph("Prepared in partial fulfilment of the<br/>WILP Dissertation/Project/Project Work Course", S["CoverSub"]), Paragraph(f"<b>Course No.: {COURSE}<br/><br/>AT<br/>{ORG}</b>", S["CoverSub"]), Spacer(1, 0.55 * inch), Paragraph("<b>BIRLA INSTITUTE OF TECHNOLOGY &amp; SCIENCE, PILANI<br/>July 2026</b>", S["CoverSub"]), PageBreak()]
    story += [h("Acknowledgements"), p(f"I express my sincere gratitude to the leadership and engineering teams at {ORG} for providing the professional environment and business context required to complete this project."), p(f"I am deeply thankful to my organization supervisor, {SUPERVISOR}, for continuous guidance, architectural review and practical inputs. I also thank {EXAMINER} for technical feedback on the data science and analytics direction of the work."), p("I am grateful to the faculty mentor and the WILP Division of BITS Pilani for the academic framework, evaluation discipline and report guidelines. I also acknowledge my colleagues, peers and family for their support during development, testing and documentation."), PageBreak()]
    rows = [
        ("Organization", ORG), ("Location", "Bangalore"), ("Duration", "January 2026 to July 2026"), ("Date of Start", "January 2026"), ("Date of Submission", "July 2026"), ("Title of the Project", f"{TITLE}: {SUBTITLE}"), ("ID No./Name of the Student", f"{BITS_ID} / {STUDENT}"), ("Supervisor and Additional Examiner", f"{SUPERVISOR}; {EXAMINER}"), ("Faculty Mentor", "To be filled as per institute record"), ("Key Words", "Recruitment analytics, medallion architecture, Azure PostgreSQL, Azure Blob Storage, Streamlit, Prefect, DuckDB, Parquet, SCD Type 2, PII encryption, NLP, Text-to-SQL, Hugging Face, Qwen2.5-Coder, Random Forest"), ("Project Areas", "Data Engineering, Data Science, Cloud Analytics, Machine Learning, Business Intelligence"),
    ]
    story += [h("Abstract Sheet")] + tbl(["Field", "Details"], rows, [1.8, 5.2]) + [h("Abstract", 2), p(ABSTRACT), Spacer(1, 0.3 * inch)] + tbl(["Signature of Student", "Signature of Supervisor"], [("Date:", "Date:")], [3.4, 3.4]) + [PageBreak()]
    story += [h("Table of Contents"), p("The report body follows the WILP decimal numbering scheme and includes the required front matter, main text, conclusions, references, glossary and appendices.")] + toc_flowables() + [PageBreak()]
    story += [
        h("1. Introduction"),
        p("Recruitment is a data-intensive function where decisions depend on candidate profiles, job requirements, interview schedules, interviewer feedback, engagement behaviour and historical changes. TalentFlow AI was developed as an enterprise-style recruitment data product that converts operational hiring events into governed analytics and predictive intelligence."),
        h("1.1 Background of the Problem", 2),
    ]
    for item in ["Candidate data is often overwritten, causing loss of historical context.", "Operational reporting directly on source tables can create inconsistent metrics and heavy joins.", "Recruitment managers need business-ready KPIs without writing SQL.", "Sensitive fields such as email, phone, password and expected salary need stronger protection.", "AI interfaces need curated, validated analytical sources to avoid unreliable answers."]:
        story.append(bullet(item))
    story += [h("1.2 Objectives", 2)]
    for item in ["Design a normalized recruitment database.", "Create a role-aware Streamlit portal.", "Build repeatable Bronze, Silver and Gold ELT flows.", "Store versioned Parquet outputs with run-level lineage.", "Encrypt PII in Silver and preserve candidate history through SCD Type 2 logic.", "Generate Gold KPIs and ML feature insights.", "Provide a guarded analytics assistant for safe read-only SQL."]:
        story.append(bullet(item))
    story += [h("1.3 Scope and Limitations", 2), p("The project includes a working portal, PostgreSQL schema, medallion lakehouse pipeline, validation scripts, Hive external table definitions, ML artifacts and analytics assistant. Current limitations include plaintext demo passwords, email-domain role checks, synthetic/demo data and the need for production monitoring and stronger model governance.")]
    story += [h("1.4 Methodology", 2)] + numbered(["Identify recruitment workflows and analytics requirements.", "Design the relational schema.", "Implement role-based portal workflows.", "Create cloud ELT pipelines and lakehouse outputs.", "Validate Gold metrics and contracts.", "Train and publish ML insights.", "Document the work according to WILP guidelines."])
    story += [h("2. Literature and Technology Background"), p("Medallion architecture organizes data through Bronze, Silver and Gold layers so quality improves progressively [1]. Azure storage patterns support storing and transforming data into Parquet for analytics [2]. Prefect flows and tasks provide Python-native orchestration with tracked workflow state [3]. Streamlit supports interactive Python data apps with widgets, charts and layout features [4]. DuckDB can query and write Parquet files directly and benefits from columnar access patterns [5][6]. scikit-learn Random Forest models provide tabular baselines and feature importance, with known caution around high-cardinality features [7]."), p("For the conversational analytics layer, Hugging Face Transformers provides a pipeline abstraction for inference. The project uses a local text-generation pipeline so SQL can be generated without paid cloud AI for every demo. The selected default model is Qwen/Qwen2.5-Coder-1.5B-Instruct, an instruction-tuned code-focused model, and Hugging Face Hub caching allows downloaded files to be reused locally after the first download [8][9][10].")]
    story += [h("3. Requirement Analysis"), h("3.1 Functional Requirements", 2)]
    story += tbl(["Requirement", "Description"], [("Candidate onboarding", "Register, login and update profile."), ("Candidate audit", "Capture profile changes."), ("Admin scheduling", "Assign candidate, job, interviewer and stage."), ("Interviewer feedback", "Submit rating, comments and decision."), ("Dashboard KPIs", "Show Gold analytics and ML insights."), ("Ask Data", "Generate and run safe read-only SQL."), ("Teach the Agent", "Store feedback and corrected SQL.")], [1.8, 5.2])
    story += [h("3.2 Non-Functional Requirements", 2)]
    for item in ["Reproducibility through shared run_datetime folders.", "PII protection before Silver publication.", "Gold data quality checks and reconciliation.", "Maintainability through table registries and helpers.", "Extensibility through Hive-compatible external table definitions."]:
        story.append(bullet(item))
    story += [h("4. System Design"), p("The architecture separates transactional work from analytical processing. PostgreSQL is the operational system, Azure Blob Storage holds lakehouse Parquet outputs, Prefect orchestrates ELT, DuckDB creates Gold metrics, Streamlit displays workflows and dashboards, and ML/agent components provide predictive and conversational intelligence.")]
    story += tbl(["Layer", "Component", "Purpose"], [("Presentation", "Streamlit portal", "Candidate, interviewer and admin interfaces"), ("Operational", "Azure PostgreSQL", "Normalized source tables and optional analytics cache"), ("Ingestion", "Bronze flow", "Raw Parquet snapshots"), ("Secure transformation", "Silver flow", "PII encryption and SCD2"), ("Analytics", "Gold flow with DuckDB", "Business KPI aggregation"), ("Consumption", "Dashboard and external tables", "KPI and BI access"), ("Intelligence", "ML and analytics agent", "Feature insights and Text-to-SQL")], [1.3, 2.1, 3.6]) + [Paragraph("Figure 1: Layered TalentFlow AI architecture.", S["Caption"])]
    story += [h("4.1 End-to-End Data Flow", 2)] + numbered(["Portal actions write to PostgreSQL.", "The full ELT flow creates one run_datetime.", "Bronze writes raw Parquet snapshots.", "Silver encrypts sensitive fields and tracks candidate history.", "Gold calculates recruitment KPIs.", "Gold can be cached into PostgreSQL for the dashboard.", "ML training writes artifacts and feature insights.", "The analytics assistant generates and validates safe SQL."])
    story += [h("5. Database Design"), p("The schema is normalized around recruitment entities. Candidate, education, job, interviewer, schedule, feedback, response, login and audit data are separated to reduce redundancy and preserve clear relationships.")]
    story += tbl(["Table", "Role"], [("candidates", "Candidate identity, contact, location, salary and signup timestamp."), ("candidate_education", "Degree, university, passing year and GPA."), ("candidate_audit_log", "Field-level profile change history."), ("login_logs", "Candidate engagement events."), ("jobs", "Job title, department, salary range and location."), ("interviewers", "Interviewer directory and specialization."), ("interview_schedules", "Candidate-job-interviewer-stage scheduling."), ("interview_feedback", "Rating, comments and decision."), ("analytics.agent_interactions", "Assistant memory and feedback.")], [2.2, 4.8])
    story += [h("5.1 Relationship Summary", 2)] + tbl(["Relationship", "Meaning"], [("candidates -> education/audit/logins", "Candidate profile, history and engagement."), ("candidates/jobs/interviewers/stages -> schedules", "Schedule connects recruitment entities."), ("schedules -> feedback", "Feedback belongs to a scheduled interview."), ("schedules/questions -> responses", "Responses connect interviews with questions.")], [2.7, 4.3]) + [Paragraph("Figure 2: Textual ER relationship summary.", S["Caption"])]
    story += [h("6. Implementation"), h("6.1 Streamlit Portal", 2), p("The portal implements login, registration, role-based routing and dashboard screens. Candidates update profiles, admins schedule interviews and inspect analytics, and interviewers submit feedback."), h("6.2 Role Handling", 2)]
    story += tbl(["Role", "Current Rule", "Main Functions"], [("Candidate", "Default non-company account", "Profile and updates"), ("Interviewer", "@altimetrik.com", "Schedule and feedback"), ("Admin", "@admin.altimetrik.com", "Scheduling, KPIs, ML and Ask Data")], [1.2, 2.4, 3.4])
    story += [p("The email-domain rule is useful for demonstration, but production deployment should use a real identity provider and RBAC.")]
    story += [h("7. Data Engineering and Lakehouse Pipeline"), p("The project uses ELT. Bronze keeps raw snapshots, Silver secures and structures data, and Gold creates business-ready metrics.")]
    story += [h("7.1 Bronze Layer", 2), p("The Bronze flow extracts registered PostgreSQL tables, writes Parquet and uploads both versioned run folders and latest copies to Azure Blob Storage.")]
    story += [h("7.2 Silver Layer", 2), p("The Silver flow encrypts PII and applies SCD Type 2-style candidate history using row_hash, start_date, end_date and is_current fields.")]
    story += tbl(["PII Table", "Protected Columns", "Behaviour"], [("candidates", "email, phone_number, password, expected_salary", "Encrypted and SCD2 enabled"), ("recruiters", "email", "Encrypted secure copy"), ("interviewers", "email", "Encrypted secure copy"), ("candidate_audit_log", "old_value, new_value", "Encrypted audit values")], [1.8, 3.0, 2.2])
    story += [h("7.3 Gold Layer", 2), p("The Gold flow reads Silver Parquet, decrypts salary only for aggregation and creates lake-first analytical datasets using DuckDB.")]
    story += tbl(["Gold Dataset", "Business Use"], [("city_talent_score", "Candidate count and average salary by city."), ("salary_benchmarks", "Average expected salary by degree."), ("candidate_engagement", "Login count per candidate."), ("interview_pipeline_funnel", "Interview count by job, stage and status."), ("job_hire_rate", "Feedback count, hire count and hire-rate percentage.")], [2.2, 4.8])
    story += [h("7.4 Hive-Compatible External Tables", 2), p("The lakehouse SQL file defines Bronze, Silver and Gold external tables partitioned by run_datetime, preparing the Parquet outputs for Spark, Synapse, Databricks SQL or similar engines.")]
    story += [h("8. Predictive Intelligence and Analytics Agent"), h("8.1 Machine Learning Pipeline", 2), p("The ML layer trains hire_prediction, decision_prediction and rating_prediction models using numeric and categorical recruitment features. Preprocessing uses imputation, scaling and one-hot encoding before Random Forest training.")]
    story += tbl(["Model", "Current Result", "Notes"], [("hire_prediction", "Accuracy 0.7552, F1 0.8427, ROC-AUC 0.8262", "Support 241"), ("decision_prediction", "Accuracy 0.7884, weighted F1 0.8165", "Hire, Hold, Reject"), ("rating_prediction", "MAE 0.3017, R2 0.5309", "Support 241")], [1.8, 3.2, 2.0])
    story += [p("These results demonstrate a functioning ML workflow. Because the data is demo-oriented, the models should be treated as decision-support prototypes and not automatic hiring decision makers."), h("8.2 Conversational Analytics Agent", 2), p("The Ask Data module is one of the most important new aspects of TalentFlow AI. It gives recruitment admins a chat-style analytics interface where they can ask natural-language questions such as which cities have the strongest candidate pipeline or which high-rated candidates were not hired. The system converts the question into safe PostgreSQL SELECT, executes it, explains the result and renders a table, metric, bar chart or line chart.")]
    story += tbl(["Component", "Responsibility"], [("analytics_assistant.py", "Schema guide, built-in question patterns and SQL safety rules."), ("local_sql_model.py", "Free local NLP matcher using weighted terms, TF-IDF style cosine scoring and learned examples."), ("huggingface_sql_agent.py", "Downloaded Hugging Face text-generation LLM for JSON SQL plans and repair prompts."), ("analytics_agent.py", "Router for schema context, learned examples, local/Hugging Face/cloud modes, narration and memory."), ("analytics.agent_interactions", "Stores question, SQL, summary, chart type, helpful flag and corrected SQL.")], [2.4, 4.6])
    story += [h("8.2.1 NLP and Local Semantic Matching", 3), p("The project does not depend only on a large language model. It includes a deterministic local NLP layer that tokenizes the user's question, removes noise words, compares the question with built-in recruitment use cases and learned examples, and selects the closest SQL template using TF-IDF style cosine similarity. This keeps common analytics questions usable even when internet access, GPU memory or paid AI keys are unavailable.")]
    for item in ["Built-in use cases include hiring summary, city pipeline strength, high-rated candidates not hired, degree performance, inactive candidates, pipeline bottlenecks and question bank coverage.", "Learned examples come from prior admin feedback where an answer was marked useful or corrected SQL was provided.", "If a user pastes SQL directly, the same read-only sanitizer is still applied before execution.", "In the latest implementation, fast local SQL mode is checked before slow LLM generation so routine questions remain responsive on normal laptops."]:
        story.append(bullet(item))
    story += [h("8.2.2 Hugging Face Downloaded LLM Mode", 3), p("Hugging Face mode is enabled when LOCAL_LLM_PROVIDER is set to hf, huggingface or transformers. The default model is Qwen/Qwen2.5-Coder-1.5B-Instruct, loaded through transformers.pipeline('text-generation') with trust_remote_code disabled, configurable CPU/GPU device selection and a configurable max_new_tokens limit. The first run may download the model from Hugging Face; later runs reuse the local cache.")]
    story += tbl(["Configuration", "Purpose"], [("LOCAL_LLM_PROVIDER", "Selects Hugging Face local LLM mode."), ("LOCAL_HF_MODEL", "Chooses the model, defaulting to Qwen/Qwen2.5-Coder-1.5B-Instruct."), ("LOCAL_HF_DEVICE", "Controls CPU/GPU target; -1 means CPU."), ("LOCAL_HF_MAX_NEW_TOKENS", "Caps generated output length."), ("LOCAL_AGENT_SPEED_MODE", "Uses fast local SQL first by default; llm_first can force Hugging Face first."), ("LOCAL_ALLOW_SLOW_LLM", "Allows slower Hugging Face fallback when local confidence is low."), ("LOCAL_FIRST_CONFIDENCE", "Controls the minimum similarity score for fast local SQL answers."), ("transformers, torch, accelerate", "Runtime dependencies for local inference.")], [2.4, 4.6])
    story += [p("Qwen2.5-Coder is suitable because Text-to-SQL is code-like: the model must reason over schema text and produce syntactically valid PostgreSQL. The prompt asks for strict JSON with title, sql, chart_type and reasoning, but the output is still parsed and sanitized before execution."), h("8.2.3 Prompt Design, Repair and Safety", 3), p("The Hugging Face prompt includes the user's question, schema context from information_schema, up to five learned examples and explicit safety rules. If the first SQL attempt fails during execution, Hugging Face mode can perform one repair pass using the original question, schema, failed SQL and database error.")]
    for item in ["Only SELECT/WITH queries are permitted.", "Only one SQL statement can be run at a time.", "Mutation keywords such as INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, COPY, GRANT and REVOKE are blocked.", "Password fields are blocked.", "A LIMIT is added when missing.", "Generated results are narrated from actual returned rows.", "Corrected SQL can teach the agent for future questions."]:
        story.append(bullet(item))
    story += [h("8.2.4 Agent Execution Flow", 3)] + numbered(["The admin enters a natural-language question or read-only SQL.", "The system builds schema context from public and analytics tables while excluding password fields.", "Useful prior examples are retrieved from analytics.agent_interactions.", "The router checks speed settings and may answer through fast local SQL before invoking the slower downloaded Hugging Face model.", "The generated SQL is sanitized, executed and optionally repaired once in Hugging Face mode.", "The result is explained, visualized and stored with feedback metadata.", "The admin can mark the answer useful or provide corrected SQL so the system learns repeated business question patterns."])
    story += [h("9. Testing, Validation and Results"), p("Testing combines offline contract tests with runtime Gold validation.")]
    story += tbl(["Validation Area", "Evidence"], [("Schema checks", "analytics schema and expected columns."), ("Row counts", "Gold tables are not empty unless allowed."), ("Null/range checks", "Counts, salary and hire-rate values are valid."), ("Duplicate checks", "Duplicate grouping keys are detected."), ("Reconciliation", "Gold totals compare with source totals."), ("Formula checks", "hire_rate_pct is recomputed and checked."), ("Contract tests", "SCD2, versioned paths, external tables, optional publish and dashboard exposure."), ("Agent tests", "Local semantic matching, Hugging Face prompt parsing, response extraction and fallback narration.")], [2.1, 4.9])
    story += [h("10. Security, Privacy and Governance"), p("PII encryption, SQL safety checks, lineage folders and validation scripts provide the project governance foundation."), h("10.1 Current Controls", 2)]
    for item in ["Fernet encryption for selected Silver PII fields.", "SCD2 candidate history.", "Read-only SQL guardrails.", "Gold reconciliation and formula validation.", "Versioned lake paths for lineage."]:
        story.append(bullet(item))
    story += [h("10.2 Production Recommendations", 2)]
    for item in ["Hash passwords using Argon2 or bcrypt.", "Move secrets to Azure Key Vault.", "Replace email-domain checks with formal RBAC.", "Add CI, monitoring and dependency scanning.", "Add model cards, fairness checks and drift monitoring."]:
        story.append(bullet(item))
    story += [h("11. Conclusions and Recommendations"), p("TalentFlow AI demonstrates a complete recruitment intelligence data product. It integrates OLTP workflows, medallion ELT, privacy handling, validated Gold KPIs, ML feature insights and conversational analytics. The strongest contribution is the combination of data engineering, governance and predictive intelligence in one coherent practical system."), p("Future work should focus on production authentication, real-world data, stronger ML validation, monitoring, deployment automation and a richer natural-language analytics experience over curated Gold data.")]
    story += [h("12. References")]
    for i, (author, title, link) in enumerate(REFERENCES, 1):
        story.append(p(f"[{i}] {author}, \"{title}\", {link}.", "Ref"))
    story += [h("13. Glossary")]
    story += tbl(["Term", "Meaning"], [("ADLS", "Azure Data Lake Storage."), ("Bronze", "Raw ingestion layer."), ("Silver", "Validated and secured layer."), ("Gold", "Business-ready analytics layer."), ("ELT", "Extract, Load and Transform."), ("PII", "Personally identifiable information."), ("SCD Type 2", "Historical row-version tracking method."), ("Parquet", "Columnar analytics file format."), ("Prefect", "Python workflow orchestration tool."), ("DuckDB", "Embedded analytical SQL engine."), ("NLP", "Natural Language Processing for interpreting admin questions."), ("Hugging Face", "Model hub and Transformers library used for local inference."), ("Local LLM", "Downloaded model run locally instead of paid cloud AI."), ("Qwen2.5-Coder", "Default code-focused model for Text-to-SQL."), ("Prompt", "Instruction text containing schema, examples, rules and user question."), ("SQL repair", "Second prompt that corrects failed SQL using the database error."), ("Feedback memory", "Stored interactions and corrected SQL used for future questions."), ("Feature importance", "Model explanation score for input features."), ("Text-to-SQL", "Natural-language to SQL conversion.")], [1.6, 5.4])
    story += [h("14. Appendices"), h("Appendix A: Main Project Files", 2)]
    story += tbl(["File", "Purpose"], [("app/portal.py", "Portal and dashboard."), ("app/analytics_agent.py", "Agent routing, schema context, narration, SQL repair and feedback memory."), ("app/local_sql_model.py", "Free local NLP matcher using weighted terms and TF-IDF cosine similarity."), ("app/huggingface_sql_agent.py", "Downloaded Hugging Face Qwen2.5-Coder Text-to-SQL generation and repair prompts."), ("pipelines/elt_bronze.py", "Bronze ingestion."), ("pipelines/elt_silver.py", "PII encryption and SCD2."), ("pipelines/elt_gold.py", "Gold KPI aggregation."), ("models/train_ml_insights.py", "ML training and publishing."), ("scripts/validate_gold_analytics.py", "Gold validation."), ("lakehouse/hive_external_tables.sql", "External table definitions."), ("tests/test_project_contracts.py", "Project contract tests.")], [2.5, 4.5])
    story += [h("Appendix B: Sample Demonstration Flow", 2)] + numbered(["Register or login as a candidate.", "Schedule an interview as admin.", "Submit feedback as interviewer.", "Run the full ELT pipeline.", "Run Gold validation.", "Train ML insights.", "Show KPIs, ML feature insights and Ask Data in the admin dashboard."])
    story += [h("Appendix C: Ethical Use Statement", 2), p("TalentFlow AI supports recruiters with better visibility and should not replace human judgement. ML outputs are decision-support signals only, and final hiring decisions must remain human-reviewed, transparent and compliant with policy.")]
    return story


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=PAGE_SIZE,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
        title=f"{TITLE}: Final Project Report",
        author=STUDENT,
    )
    doc.build(build_story(), onFirstPage=footer, onLaterPages=footer)


def extract_toc_pages(pdf_path):
    import pdfplumber

    pages = {}
    with pdfplumber.open(str(pdf_path)) as pdf:
        for physical_index, page in enumerate(pdf.pages, start=1):
            if physical_index < BODY_START_PHYSICAL_PAGE:
                continue
            text = page.extract_text() or ""
            for entry in TOC_ENTRIES:
                if entry not in pages and entry in text:
                    pages[entry] = physical_index - BODY_START_PHYSICAL_PAGE + 1
    return pages


def extract_body_start_page(pdf_path):
    import pdfplumber

    with pdfplumber.open(str(pdf_path)) as pdf:
        for physical_index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if (
                "1. Introduction" in text
                and "Recruitment is a data-intensive function" in text
                and "Table of Contents" not in text
            ):
                return physical_index
    return BODY_START_PHYSICAL_PAGE


def main():
    global TOC_PAGE_NUMBERS, BODY_START_PHYSICAL_PAGE
    build_pdf(OUT)
    BODY_START_PHYSICAL_PAGE = extract_body_start_page(OUT)
    TOC_PAGE_NUMBERS = extract_toc_pages(OUT)
    build_pdf(OUT)
    BODY_START_PHYSICAL_PAGE = extract_body_start_page(OUT)
    TOC_PAGE_NUMBERS = extract_toc_pages(OUT)
    build_pdf(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
