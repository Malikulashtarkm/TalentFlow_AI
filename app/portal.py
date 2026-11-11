import streamlit as st
import os
from decimal import Decimal
import psycopg2
from psycopg2 import pool, extras
from dotenv import load_dotenv
import time
import pandas as pd
from analytics_agent import (
    ensure_agent_tables,
    generate_agent_plan,
    generate_result_narrative,
    repair_agent_plan,
    record_agent_interaction,
    update_agent_feedback,
)
from analytics_assistant import schema_markdown
from genai_agent_orchestrator import build_full_hiring_pack, run_genai_agent_team, serialize_agent_run
from genai_hiring_copilot import (
    ensure_genai_tables,
    record_agent_run,
    record_copilot_output,
)

load_dotenv("config/.env")

@st.cache_resource
def init_connection_pool():
    """Keep a small PostgreSQL pool alive for the Streamlit session."""
    try:
        return psycopg2.pool.SimpleConnectionPool(
            minconn=1, 
            maxconn=10, 
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            port=os.environ.get("DB_PORT")
        )
    except Exception as e:
        st.error(f"Critical Error initializing DB Pool: {e}")
        return None

db_pool = init_connection_pool()

def get_db_connection():
    """Borrow a database connection, with a short retry for network hiccups."""
    retries = 3
    for i in range(retries):
        try:
            if db_pool is None:
                return None
            conn = db_pool.getconn()
            return conn
        except Exception as e:
            if i < retries - 1:
                time.sleep(1)
                continue
            else:
                st.error(f"Network Error: Unable to reach Azure after {retries} attempts.")
                return None

def release_db_connection(conn):
    """Return the connection to the shared pool."""
    if conn:
        db_pool.putconn(conn)

def render_assistant_result(rows, chart_type="auto"):
    """Show assistant results as metrics, a table, and a helpful chart when possible."""
    if not rows:
        st.info("No rows matched this question.")
        return

    df = pd.DataFrame(rows)
    for column in df.columns:
        if df[column].map(lambda value: isinstance(value, Decimal)).any():
            df[column] = pd.to_numeric(df[column], errors="coerce")
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    datetime_columns = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    category_columns = [
        col for col in df.columns
        if col not in numeric_columns and col not in datetime_columns
    ]

    st.dataframe(df, use_container_width=True)

    if chart_type == "table":
        return

    if (chart_type in {"auto", "metric"} and len(df) == 1 and numeric_columns):
        metric_cols = st.columns(min(len(numeric_columns), 4))
        for index, column in enumerate(numeric_columns[:4]):
            metric_cols[index].metric(column.replace("_", " ").title(), df.iloc[0][column])
        return

    if chart_type in {"auto", "line"} and datetime_columns and numeric_columns:
        chart_df = df[[datetime_columns[0], numeric_columns[0]]].dropna()
        if not chart_df.empty:
            st.line_chart(chart_df.set_index(datetime_columns[0]))
        return

    if chart_type in {"auto", "bar"} and category_columns and numeric_columns:
        chart_df = df[[category_columns[0], numeric_columns[0]]].dropna().head(25)
        if not chart_df.empty:
            st.bar_chart(chart_df.set_index(category_columns[0]))

st.set_page_config(page_title="TalentFlow AI", page_icon="💼", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { 
        width: 100%; 
        border-radius: 5px; 
        height: 3em; 
        background-color: #003366; 
        color: white; 
        font-weight: bold;
    }
    .stTextInput>div>div>input { border-radius: 5px; }
    h1, h2, h3 { color: #003366; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/912/912214.png", width=80)
    st.title("TalentFlow AI")
    st.markdown("---")
    
    if st.session_state.logged_in:
        st.write(f"Logged in as: **{st.session_state.user_email}**")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.rerun()
    else:
        st.info("Please Login or Register to access the portal.")

if not st.session_state.logged_in:
    menu = st.radio("Choose Action", ["Login", "Register"], horizontal=True)

    if menu == "Login":
        st.title("👋 Welcome Back")
        with st.container():
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                if st.button("Sign In"):
                    try:
                        conn = get_db_connection()
                        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
                        cur.execute("SELECT candidate_id FROM candidates WHERE email = %s AND password = %s", (email, password))
                        user = cur.fetchone()
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user['candidate_id']
                            st.session_state.user_email = email
                            cur.execute("INSERT INTO login_logs (candidate_id) VALUES (%s)", (user['candidate_id'],))
                            conn.commit()
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
                        cur.close()
                        release_db_connection(conn)
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

    else:
        st.title("📝 Create Account")
        with st.container():
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                reg_email = st.text_input("Email Address")
                reg_password = st.text_input("Create Password", type="password")
                st.markdown("---")
                f_name = st.text_input("First Name")
                l_name = st.text_input("Last Name")
                phone = st.text_input("Phone Number")
                city = st.text_input("City")
                state = st.text_input("State")
                country = st.text_input("Country", value="India")
                st.markdown("---")
                degree = st.text_input("Highest Degree (e.g. M.Tech)")
                univ = st.text_input("University")
                year = st.number_input("Passing Year", min_value=1900, max_value=2030, value=2026)
                gpa = st.number_input("GPA/Percentage", format="%.2f")
                
                if st.button("Register"):
                    if reg_email and reg_password and f_name:
                        try:
                            conn = get_db_connection()
                            cur = conn.cursor(cursor_factory=extras.RealDictCursor)
                            cur.execute(
                                "INSERT INTO candidates (email, password, first_name, last_name, phone_number, city, state, country) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING candidate_id",
                                (reg_email, reg_password, f_name, l_name, phone, city, state, country)
                            )
                            user_id = cur.fetchone()['candidate_id']
                            cur.execute(
                                "INSERT INTO candidate_education (candidate_id, degree, university, passing_year, gpa) VALUES (%s, %s, %s, %s, %s)",
                                (user_id, degree, univ, year, gpa)
                            )
                            conn.commit()
                            st.success("✅ Account created! Please Login.")
                            cur.close()
                            release_db_connection(conn)
                        except Exception as e:
                            st.error(f"Registration failed: {e}")
                    else:
                        st.error("Please fill all required fields.")

else:
    if st.session_state.user_email.endswith("@admin.altimetrik.com"):
        st.title("🛠️ Recruitment Admin Center")
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=extras.RealDictCursor)
            tab_sch, tab_view, tab_genai, tab_ask = st.tabs(["Schedule Interview", "Pipeline Overview", "GenAI Copilot", "Ask Data"])
            with tab_sch:
                st.subheader("Create New Interview Schedule")
                with st.form("schedule_form"):
                    cur.execute("SELECT candidate_id, first_name, last_name FROM candidates")
                    candidates = cur.fetchall()
                    cand_map = {f"{c['first_name']} {c['last_name']}": c['candidate_id'] for c in candidates}
                    selected_cand = st.selectbox("Select Candidate", options=list(cand_map.keys()))
                    cur.execute("SELECT job_id, job_title FROM jobs")
                    jobs = cur.fetchall()
                    job_map = {j['job_title']: j['job_id'] for j in jobs}
                    selected_job = st.selectbox("Select Job Role", options=list(job_map.keys()))
                    cur.execute("SELECT interviewer_id, full_name FROM interviewers")
                    interviewers = cur.fetchall()
                    int_map = {i['full_name']: i['interviewer_id'] for i in interviewers}
                    selected_int = st.selectbox("Assign Interviewer", options=list(int_map.keys()))
                    cur.execute("SELECT stage_id, stage_name FROM interview_stages")
                    stages = cur.fetchall()
                    stage_map = {s['stage_name']: s['stage_id'] for s in stages}
                    selected_stage = st.selectbox("Interview Stage", options=list(stage_map.keys()))
                    int_date = st.date_input("Interview Date")
                    int_time = st.time_input("Interview Time")
                    submit_sch = st.form_submit_button("Schedule Interview")
                    if submit_sch:
                        full_datetime = f"{int_date} {int_time}"
                        cur.execute("""
                            INSERT INTO interview_schedules (candidate_id, job_id, interviewer_id, stage_id, interview_date)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (cand_map[selected_cand], job_map[selected_job], int_map[selected_int], stage_map[selected_stage], full_datetime))
                        conn.commit()
                        st.success(f"✅ Interview scheduled for {selected_cand}!")
                        st.rerun()
            with tab_view:
                st.subheader("Current Hiring Pipeline")
                cur.execute("""
                    SELECT s.schedule_id, c.first_name, c.last_name, j.job_title, st.stage_name, s.status
                    FROM interview_schedules s
                    JOIN candidates c ON s.candidate_id = c.candidate_id
                    JOIN jobs j ON s.job_id = j.job_id
                    JOIN interview_stages st ON s.stage_id = st.stage_id
                """)
                pipeline = cur.fetchall()
                if pipeline: st.table(pipeline)
                else: st.info("No interviews scheduled yet.")
                st.markdown("---")
                st.subheader("Gold Layer KPIs")
                kpi_queries = {
                    "Hire Rate by Job": """
                        SELECT job_title, total_feedback, hire_count, hire_rate_pct
                        FROM analytics.job_hire_rate
                        ORDER BY hire_rate_pct DESC
                    """,
                    "Pipeline Funnel": """
                        SELECT job_title, stage_name, status, interview_count
                        FROM analytics.interview_pipeline_funnel
                        ORDER BY job_title, stage_name, status
                    """,
                    "Salary Benchmarks": """
                        SELECT degree, avg_expected
                        FROM analytics.salary_benchmarks
                        ORDER BY avg_expected DESC
                    """,
                    "City Talent Score": """
                        SELECT city, candidate_count, avg_salary
                        FROM analytics.city_talent_score
                        ORDER BY candidate_count DESC
                        LIMIT 15
                    """,
                }
                kpi_tabs = st.tabs(list(kpi_queries.keys()))
                for kpi_tab, (label, query) in zip(kpi_tabs, kpi_queries.items()):
                    with kpi_tab:
                        try:
                            cur.execute(query)
                            rows = cur.fetchall()
                            if rows:
                                st.dataframe(rows, use_container_width=True)
                            else:
                                st.info(f"No rows found for {label}. Run the ELT pipeline first.")
                        except Exception:
                            st.warning(f"{label} is not available yet. Run the gold pipeline.")

                st.subheader("ML Feature Insights")
                try:
                    cur.execute("""
                        SELECT model_name, feature_rank, feature, importance
                        FROM analytics.ml_feature_insights
                        ORDER BY model_name, feature_rank
                        LIMIT 45
                    """)
                    ml_rows = cur.fetchall()
                    if ml_rows:
                        st.dataframe(ml_rows, use_container_width=True)
                    else:
                        st.info("No ML insights found. Train models to publish feature importance.")
                except Exception:
                    st.warning("ML insights are not available yet. Run models/train_ml_insights.py.")
            with tab_genai:
                ensure_genai_tables(cur)
                conn.commit()
                st.subheader("GenAI agent studio")
                st.caption("Run specialist agents for recruiting content, interview design, analytics planning, and guardrail review.")

                cur.execute(
                    """
                    SELECT c.candidate_id, c.first_name, c.last_name, c.city, c.state, e.degree, e.university, e.gpa
                    FROM candidates c
                    LEFT JOIN candidate_education e ON e.candidate_id = c.candidate_id
                    ORDER BY c.created_at DESC
                    """
                )
                copilot_candidates = cur.fetchall()
                cur.execute("SELECT job_id, job_title, department, salary_range, job_location FROM jobs ORDER BY job_title")
                copilot_jobs = cur.fetchall()
                cur.execute("SELECT stage_name FROM interview_stages ORDER BY stage_id")
                copilot_stages = [row["stage_name"] for row in cur.fetchall()]

                if not copilot_candidates or not copilot_jobs:
                    st.info("Add candidates and jobs before generating hiring artifacts.")
                else:
                    candidate_options = {
                        f"{row['first_name']} {row['last_name']} | {row.get('degree') or 'Profile'} | {row.get('city') or 'Unknown city'}": row
                        for row in copilot_candidates
                    }
                    job_options = {f"{row['job_title']} | {row.get('job_location') or 'Location TBD'}": row for row in copilot_jobs}
                    selected_candidate_label = st.selectbox("Candidate context", list(candidate_options.keys()))
                    selected_job_label = st.selectbox("Role context", list(job_options.keys()))
                    selected_stage_name = st.selectbox("Interview stage", copilot_stages or ["Technical"])

                    agent_prompt = st.text_area(
                        "Agent request",
                        value="Create recruiter outreach, an interview kit, a feedback summary, analytics next steps, and risk review.",
                        height=90,
                    )

                    with st.container(horizontal=True):
                        generate_pack = st.button("Generate hiring pack", icon=":material/auto_awesome:")
                        run_agent_team = st.button("Run agent team", icon=":material/hub:")

                    if generate_pack or run_agent_team:
                        selected_candidate = candidate_options[selected_candidate_label]
                        selected_job = job_options[selected_job_label]
                        cur.execute(
                            """
                            SELECT f.rating, f.comments, f.decision
                            FROM interview_feedback f
                            JOIN interview_schedules s ON s.schedule_id = f.schedule_id
                            WHERE s.candidate_id = %s AND s.job_id = %s
                            ORDER BY f.submitted_at DESC
                            LIMIT 10
                            """,
                            (selected_candidate["candidate_id"], selected_job["job_id"]),
                        )
                        feedback_rows = cur.fetchall()

                    if generate_pack:
                        pack = build_full_hiring_pack(selected_candidate, selected_job, selected_stage_name, feedback_rows)
                        st.session_state.genai_copilot_pack = pack

                        combined_content = "\n\n---\n\n".join(
                            [
                                pack["job_description"],
                                pack["candidate_outreach"],
                                "\n".join(f"{item['question']}\nRubric: {item['rubric']}" for item in pack["interview_kit"]),
                                pack["feedback_summary"],
                            ]
                        )
                        output_id = record_copilot_output(
                            cur,
                            st.session_state.user_email,
                            "hiring_copilot_pack",
                            pack["context"],
                            combined_content,
                            pack["guardrail_notes"],
                        )
                        conn.commit()
                        st.success(f"Generated and stored copilot pack #{output_id}.")

                    if run_agent_team:
                        run = run_genai_agent_team(
                            agent_prompt,
                            candidate=selected_candidate,
                            job=selected_job,
                            stage_name=selected_stage_name,
                            feedback_rows=feedback_rows,
                        )
                        serialized_run = serialize_agent_run(run)
                        run_id = record_agent_run(cur, st.session_state.user_email, agent_prompt, serialized_run)
                        conn.commit()
                        st.session_state.genai_agent_run = serialized_run
                        st.success(f"Agent run #{run_id} stored with guardrail score {run.guardrail_score}/100.")

                pack = st.session_state.get("genai_copilot_pack")
                if pack:
                    if pack.get("risk_report"):
                        score = pack["risk_report"]["score"]
                        st.metric("Guardrail score", f"{score}/100")
                        with st.expander("Risk findings"):
                            for finding in pack["risk_report"]["findings"]:
                                st.write(f"- {finding}")
                    st.markdown("**Job description draft**")
                    st.text_area("Job description draft", value=pack["job_description"], height=260, label_visibility="collapsed")
                    st.markdown("**Candidate outreach draft**")
                    st.text_area("Candidate outreach draft", value=pack["candidate_outreach"], height=180, label_visibility="collapsed")
                    st.markdown("**Interview kit**")
                    for item in pack["interview_kit"]:
                        with st.container(border=True):
                            st.write(item["question"])
                            st.caption(item["rubric"])
                    st.markdown("**Feedback summary**")
                    st.info(pack["feedback_summary"])
                    if pack.get("agent_trace"):
                        with st.expander("Agent trace"):
                            for event in pack["agent_trace"]:
                                st.write(f"**{event['agent_name']}** ({event['role']}): {event['content']}")
                    st.caption(pack["guardrail_notes"])

                agent_run = st.session_state.get("genai_agent_run")
                if agent_run:
                    st.markdown("---")
                    st.markdown("**Latest multi-agent run**")
                    st.info(agent_run["final_answer"])
                    st.metric("Run guardrail score", f"{agent_run['guardrail_score']}/100")
                    with st.expander("Agent trace", expanded=True):
                        for event in agent_run["trace"]:
                            st.write(f"**{event['agent_name']}** ({event['role']}): {event['content']}")
                    if agent_run["artifacts"].get("analytics_plan"):
                        with st.expander("Analytics plan"):
                            plan = agent_run["artifacts"]["analytics_plan"]
                            st.write(plan["title"])
                            if plan.get("sql"):
                                st.code(plan["sql"], language="sql")
            with tab_ask:
                ensure_agent_tables(cur)
                conn.commit()
                st.subheader("Conversational Analytics Agent")
                st.caption("Ask across candidates, jobs, interviews, feedback, activity logs, and published analytics tables.")

                if os.environ.get("LOCAL_LLM_PROVIDER", "").lower() in {"hf", "huggingface", "transformers"}:
                    if os.environ.get("LOCAL_AGENT_SPEED_MODE", "fast").lower() == "fast":
                        st.success("Fast local SQL mode is active. Hugging Face is available only if you enable slow fallback.")
                    else:
                        st.success(f"Hugging Face local LLM mode is active using {os.environ.get('LOCAL_HF_MODEL', 'Qwen/Qwen2.5-Coder-1.5B-Instruct')}.")
                elif os.environ.get("LOCAL_AGENT_ONLY", "").lower() in {"1", "true", "yes"}:
                    st.success("Free local model mode is active. The agent learns from built-in use cases and your feedback.")
                elif os.environ.get("OPENAI_API_KEY"):
                    st.success(f"AI mode is active using {os.environ.get('OPENAI_MODEL', 'gpt-5')}.")
                else:
                    st.success("Free local model mode is active. Add OPENAI_API_KEY only if you want optional cloud AI.")

                example_questions = [
                    "Give me a hiring summary with the main KPIs",
                    "Which cities have the strongest candidate pipeline?",
                    "Which candidates have high ratings but were not hired?",
                    "Which jobs have the best hire rate and enough feedback?",
                    "Which interviewers have the highest pending feedback workload?",
                    "Which degrees are associated with better ratings?",
                    "Which active candidates have not logged in recently?",
                    "What are the top ML feature insights and what should I do next?",
                ]
                selected_example = st.selectbox("Example questions", [""] + example_questions)
                default_question = selected_example or st.session_state.get("assistant_question", "")
                question = st.text_area(
                    "Question or read-only SQL",
                    value=default_question,
                    height=110,
                    placeholder="Ask a recruitment question, or paste a SELECT/WITH query.",
                )

                with st.expander("Available data"):
                    st.markdown(schema_markdown())

                if st.button("Run Agent"):
                    st.session_state.assistant_question = question
                    try:
                        result_slot = st.container(border=True)
                        with st.status("Running the analytics agent...", expanded=True) as status:
                            st.write("Preparing schema and learned examples.")
                            st.write("Checking fast local SQL patterns before any slow LLM generation.")
                            plan = generate_agent_plan(cur, question, st.session_state.user_email)
                            st.write(f"Generated plan using {plan.get('mode', 'Agent')}.")

                            st.write("Executing the SQL safely against PostgreSQL.")
                            try:
                                cur.execute(plan["sql"])
                                rows = cur.fetchall()
                            except Exception as sql_error:
                                conn.rollback()
                                st.write("The first SQL attempt failed. Trying one repair pass.")
                                with st.expander("Failed SQL", expanded=True):
                                    st.code(plan["sql"], language="sql")
                                    st.caption(str(sql_error))
                                plan = repair_agent_plan(cur, question, plan, str(sql_error))
                                cur.execute(plan["sql"])
                                rows = cur.fetchall()

                            st.write("Explaining the result and preparing visuals.")
                            narrative = generate_result_narrative(question, plan["sql"], rows, plan)

                            interaction_id = record_agent_interaction(
                                cur,
                                st.session_state.user_email,
                                question,
                                plan,
                                narrative,
                                len(rows),
                            )
                            conn.commit()
                            st.session_state.last_agent_interaction_id = interaction_id
                            status.update(label="Agent run complete.", state="complete")

                        with result_slot:
                            st.markdown(f"**Answer:** {plan['title']}")
                            st.caption(f"Mode: {plan.get('mode', 'Agent')} | Visual: {plan.get('chart_type', 'auto')}")
                            if plan.get("reasoning"):
                                st.write(plan["reasoning"])
                            with st.expander("Generated SQL", expanded=True):
                                st.code(plan["sql"], language="sql")
                            st.write(narrative)
                            render_assistant_result(rows, plan.get("chart_type", "auto"))
                    except Exception as e:
                        st.error(f"Assistant could not answer this safely: {e}")

                if st.session_state.get("last_agent_interaction_id"):
                    st.markdown("---")
                    st.subheader("Teach the Agent")
                    corrected_sql = st.text_area(
                        "Optional corrected SQL",
                        height=90,
                        placeholder="Paste a better SELECT/WITH query if the answer needs correction.",
                    )
                    col_good, col_bad = st.columns(2)
                    with col_good:
                        if st.button("This was useful"):
                            update_agent_feedback(cur, st.session_state.last_agent_interaction_id, True, corrected_sql)
                            conn.commit()
                            st.success("Saved. The agent can use this as a future example.")
                    with col_bad:
                        if st.button("Needs improvement"):
                            update_agent_feedback(cur, st.session_state.last_agent_interaction_id, False, corrected_sql)
                            conn.commit()
                            st.info("Feedback saved. Add corrected SQL to teach the agent the better route.")
            cur.close()
            release_db_connection(conn)
        except Exception as e:
            st.error(f"Admin Portal Error: {e}")

    elif st.session_state.user_email.endswith("@altimetrik.com"):
        st.title("👨‍💼 Interviewer Control Center")
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=extras.RealDictCursor)
            cur.execute("SELECT interviewer_id FROM interviewers WHERE LOWER(email) = LOWER(%s)", (st.session_state.user_email,))
            interviewer_res = cur.fetchone()
            if not interviewer_res:
                st.error("❌ Profile missing from interviewers table.")
            else:
                int_id = interviewer_res['interviewer_id']
                st.subheader("📅 Today's Interview Schedule")
                cur.execute("""
                    SELECT s.schedule_id, c.first_name, c.last_name, j.job_title, st.stage_name, s.status
                    FROM interview_schedules s
                    JOIN candidates c ON s.candidate_id = c.candidate_id
                    JOIN jobs j ON s.job_id = j.job_id
                    JOIN interview_stages st ON s.stage_id = st.stage_id
                    WHERE s.interviewer_id = %s
                """, (int_id,))
                schedules = cur.fetchall()
                if not schedules:
                    st.info("No interviews scheduled for you today.")
                else:
                    for sch in schedules:
                        with st.expander(f"Candidate: {sch['first_name']} {sch['last_name']} - {sch['job_title']}"):
                            st.write(f"**Stage:** {sch['stage_name']} | **Status:** {sch['status']}")
                            with st.form(key=f"feedback_{sch['schedule_id']}"):
                                rating = st.slider("Rating (1-5)", 1, 5, 3)
                                comments = st.text_area("Technical Feedback")
                                decision = st.selectbox("Decision", ["Hire", "Hold", "Reject"])
                                if st.form_submit_button("Submit Feedback"):
                                    cur.execute("INSERT INTO interview_feedback (schedule_id, rating, comments, decision) VALUES (%s, %s, %s, %s)", (sch['schedule_id'], rating, comments, decision))
                                    cur.execute("UPDATE interview_schedules SET status = 'Completed' WHERE schedule_id = %s", (sch['schedule_id'],))
                                    conn.commit()
                                    st.success("Feedback submitted!")
                                    st.rerun()
            cur.close()
            release_db_connection(conn)
        except Exception as e:
            st.error(f"Interviewer Portal Error: {e}")

    else:
        st.title("👤 Candidate Dashboard")
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=extras.RealDictCursor)
            cur.execute("SELECT c.*, e.degree, e.university, e.passing_year, e.gpa FROM candidates c JOIN candidate_education e ON c.candidate_id = e.candidate_id WHERE c.candidate_id = %s", (st.session_state.user_id,))
            user_data = cur.fetchone()
            if user_data:
                st.write(f"Welcome back, **{user_data['first_name']} {user_data['last_name']}**!")
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"📍 **Location:** {user_data['city']}, {user_data['state']}")
                    st.info(f"🎓 **Education:** {user_data['degree']} from {user_data['university']}")
                with col2:
                    st.info(f"📧 **Email:** {user_data['email']}")
                    st.info(f"📞 **Phone:** {user_data['phone_number']}")
                st.markdown("---")
                st.subheader("⚙️ Update Profile")
                with st.form("update_profile_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_phone = st.text_input("Phone Number", value=user_data['phone_number'])
                        new_city = st.text_input("City", value=user_data['city'])
                        new_state = st.text_input("State", value=user_data['state'])
                    with c2:
                        new_degree = st.text_input("Degree", value=user_data['degree'])
                        new_univ = st.text_input("University", value=user_data['university'])
                        new_gpa = st.number_input("GPA", value=float(user_data['gpa']) if user_data['gpa'] else 0.0)
                    submit_update = st.form_submit_button("Save Changes")
                if submit_update:
                    changes = {"phone_number": new_phone, "city": new_city, "state": new_state, "degree": new_degree, "university": new_univ, "gpa": new_gpa}
                    updates_to_candidate, updates_to_education, logs_to_insert = {}, {}, []
                    for field, new_val in changes.items():
                        if field in ['phone_number', 'city', 'state']:
                            old_val = user_data.get(field)
                            if new_val != old_val:
                                logs_to_insert.append((st.session_state.user_id, field, str(old_val), str(new_val)))
                                updates_to_candidate[field] = new_val
                        elif field in ['degree', 'university', 'gpa']:
                            old_val = user_data.get(field)
                            if new_val != old_val:
                                logs_to_insert.append((st.session_state.user_id, field, str(old_val), str(new_val)))
                                updates_to_education[field] = new_val
                    if logs_to_insert:
                        cur.executemany("INSERT INTO candidate_audit_log (candidate_id, field_changed, old_value, new_value) VALUES (%s, %s, %s, %s)", logs_to_insert)
                        if updates_to_candidate:
                            set_clause = ", ".join([f"{k} = %s" for k in updates_to_candidate.keys()])
                            cur.execute(f"UPDATE candidates SET {set_clause} WHERE candidate_id = %s", list(updates_to_candidate.values()) + [st.session_state.user_id])
                        if updates_to_education:
                            set_clause = ", ".join([f"{k} = %s" for k in updates_to_education.keys()])
                            cur.execute(f"UPDATE candidate_education SET {set_clause} WHERE candidate_id = %s", list(updates_to_education.values()) + [st.session_state.user_id])
                        conn.commit()
                        st.success("✅ Profile updated!")
                        st.rerun()
            cur.close()
            release_db_connection(conn)
        except Exception as e:
            st.error(f"Error: {e}")
