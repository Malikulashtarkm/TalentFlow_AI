import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("config/.env")

def repair():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            port=os.environ.get("DB_PORT")
        )
        cur = conn.cursor()

        # 1. Check what tables actually exist
        print("🔍 Checking existing tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        existing_tables = [row[0] for row in cur.fetchall()]
        print(f"Found tables: {existing_tables}")

        # 2. The Master Schema (Simplified version for the repair)
        # I'm adding "IF NOT EXISTS" to every single one
        schema_commands = [
            "CREATE TABLE IF NOT EXISTS candidates (candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), email TEXT UNIQUE NOT NULL, first_name TEXT NOT NULL, last_name TEXT NOT NULL, phone_number TEXT, city TEXT, state TEXT, country TEXT, password TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());",
            "CREATE TABLE IF NOT EXISTS candidate_education (edu_id SERIAL PRIMARY KEY, candidate_id UUID REFERENCES candidates(candidate_id), degree TEXT, university TEXT, passing_year INTEGER, gpa NUMERIC);",
            "CREATE TABLE IF NOT EXISTS candidate_audit_log (audit_id SERIAL PRIMARY KEY, candidate_id UUID REFERENCES candidates(candidate_id), field_changed TEXT, old_value TEXT, new_value TEXT, changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());",
            "CREATE TABLE IF NOT EXISTS login_logs (log_id SERIAL PRIMARY KEY, candidate_id UUID REFERENCES candidates(candidate_id), login_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW());",
            "CREATE TABLE IF NOT EXISTS jobs (job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), job_title TEXT NOT NULL, department TEXT, salary_range TEXT, job_location TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());",
            "CREATE TABLE IF NOT EXISTS recruiters (recruiter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), full_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, region TEXT);",
            "CREATE TABLE IF NOT EXISTS interviewers (interviewer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), full_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, specialization TEXT);",
            "CREATE TABLE IF NOT EXISTS interview_stages (stage_id SERIAL PRIMARY KEY, stage_name TEXT NOT NULL);",
            "CREATE TABLE IF NOT EXISTS questions_bank (question_id SERIAL PRIMARY KEY, job_title TEXT, question_text TEXT NOT NULL, category TEXT);",
            "CREATE TABLE IF NOT EXISTS interview_schedules (schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), candidate_id UUID REFERENCES candidates(candidate_id), job_id UUID REFERENCES jobs(job_id), interviewer_id UUID REFERENCES interviewers(interviewer_id), stage_id INTEGER REFERENCES interview_stages(stage_id), interview_date TIMESTAMP WITH TIME ZONE, status TEXT DEFAULT 'Scheduled');",
            "CREATE TABLE IF NOT EXISTS interview_feedback (feedback_id SERIAL PRIMARY KEY, schedule_id UUID REFERENCES interview_schedules(schedule_id), rating INTEGER CHECK (rating >= 1 AND rating <= 5), comments TEXT, decision TEXT, submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());",
            "CREATE TABLE IF NOT EXISTS candidate_responses (response_id SERIAL PRIMARY KEY, schedule_id UUID REFERENCES interview_schedules(schedule_id), question_id INTEGER REFERENCES questions_bank(question_id), answer_text TEXT, submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());"
        ]

        print("🛠️ Repairing missing tables...")
        for cmd in schema_commands:
            cur.execute(cmd)
        
        conn.commit()
        print("✅ Database Repair Complete! All tables are now verified and present.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Repair Failed: {e}")

if __name__ == "__main__":
    repair()