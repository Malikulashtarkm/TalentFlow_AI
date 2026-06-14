import os
import psycopg2
from dotenv import load_dotenv

# Load secrets
load_dotenv("config/.env")

# The Master Enterprise Schema
SQL_SCHEMA = """
-- 1. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_title TEXT NOT NULL,
    department TEXT,
    salary_range TEXT,
    job_location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Recruiters Table
CREATE TABLE IF NOT EXISTS recruiters (
    recruiter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    region TEXT
);

-- 3. Interviewers Table
CREATE TABLE IF NOT EXISTS interviewers (
    interviewer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    specialization TEXT
);

-- 4. Candidates (Personal Details)
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone_number TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Candidate Education
CREATE TABLE IF NOT EXISTS candidate_education (
    edu_id SERIAL PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(candidate_id),
    degree TEXT,
    university TEXT,
    passing_year INTEGER,
    gpa NUMERIC
);

-- 6. Interview Stages
CREATE TABLE IF NOT EXISTS interview_stages (
    stage_id SERIAL PRIMARY KEY,
    stage_name TEXT NOT NULL 
);

-- 7. Questions Bank
CREATE TABLE IF NOT EXISTS questions_bank (
    question_id SERIAL PRIMARY KEY,
    job_title TEXT, 
    question_text TEXT NOT NULL,
    category TEXT
);

-- 8. Interview Schedules
CREATE TABLE IF NOT EXISTS interview_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(candidate_id),
    job_id UUID REFERENCES jobs(job_id),
    interviewer_id UUID REFERENCES interviewers(interviewer_id),
    stage_id INTEGER REFERENCES interview_stages(stage_id),
    interview_date TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'Scheduled'
);

-- 9. Interview Feedback
CREATE TABLE IF NOT EXISTS interview_feedback (
    feedback_id SERIAL PRIMARY KEY,
    schedule_id UUID REFERENCES interview_schedules(schedule_id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    decision TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. Candidate Responses
CREATE TABLE IF NOT EXISTS candidate_responses (
    response_id SERIAL PRIMARY KEY,
    schedule_id UUID REFERENCES interview_schedules(schedule_id),
    question_id INTEGER REFERENCES questions_bank(question_id),
    answer_text TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. Login Logs
CREATE TABLE IF NOT EXISTS login_logs (
    log_id SERIAL PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(candidate_id),
    login_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

def deploy():
    try:
        # Connect to Azure
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            port=os.environ.get("DB_PORT")
        )
        # Create a cursor to execute commands
        cur = conn.cursor()
        
        print("🚀 Deploying Enterprise Schema to Azure...")
        cur.execute(SQL_SCHEMA)
        
        # Commit changes to the database
        conn.commit()
        
        print("✅ Success! All 11 tables have been created in Azure PostgreSQL.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Deployment Failed: {e}")

if __name__ == "__main__":
    deploy()