import streamlit as st
import os
import psycopg2
from psycopg2 import pool, extras
from dotenv import load_dotenv
import time

# =============================================================================
# 1. SETUP & DATABASE CONNECTION POOLING
# =============================================================================
load_dotenv("config/.env")

@st.cache_resource
def init_connection_pool():
    """Initializes a permanent pool of connections to Azure PostgreSQL to prevent DNS flickers."""
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

# Initialize the pool globally
db_pool = init_connection_pool()

def get_db_connection():
    """Borrows a connection from the pool with a retry mechanism for network stability."""
    retries = 3
    for i in range(retries):
        try:
            if db_pool is None:
                return None
            conn = db_pool.getconn()
            return conn
        except Exception as e:
            if i < retries - 1:
                time.sleep(1) # Wait 1 second before retrying
                continue
            else:
                st.error(f"Network Error: Unable to reach Azure after {retries} attempts.")
                return None

def release_db_connection(conn):
    """Returns the connection back to the pool instead of closing it."""
    if conn:
        db_pool.putconn(conn)

# Page configuration
st.set_page_config(page_title="TalentFlow AI", page_icon="💼", layout="wide")

# --- PROFESSIONAL CORPORATE CSS ---
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

# =============================================================================
# 2. SESSION STATE MANAGEMENT
# =============================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# =============================================================================
# 3. NAVIGATION SIDEBAR
# =============================================================================
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

# =============================================================================
# 4. MAIN APPLICATION LOGIC
# =============================================================================

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
        # --- ADMIN DASHBOARD ---
        st.title("🛠️ Recruitment Admin Center")
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=extras.RealDictCursor)
            tab_sch, tab_view = st.tabs(["📅 Schedule Interview", "📊 Pipeline Overview"])
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
            cur.close()
            release_db_connection(conn)
        except Exception as e:
            st.error(f"Admin Portal Error: {e}")

    elif st.session_state.user_email.endswith("@altimetrik.com"):
        # --- INTERVIEWER DASHBOARD ---
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
        # --- CANDIDATE DASHBOARD ---
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