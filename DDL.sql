CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_title TEXT NOT NULL,
    department TEXT,
    salary_range TEXT,
    job_location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recruiters (
    recruiter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    region TEXT
);

CREATE TABLE IF NOT EXISTS interviewers (
    interviewer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    specialization TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone_number TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    expected_salary NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidate_education (
    edu_id SERIAL PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(candidate_id),
    degree TEXT,
    university TEXT,
    passing_year INTEGER,
    gpa NUMERIC
);

CREATE TABLE IF NOT EXISTS candidate_audit_log (
    audit_id SERIAL PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(candidate_id),
    field_changed TEXT,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_stages (
    stage_id SERIAL PRIMARY KEY,
    stage_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions_bank (
    question_id SERIAL PRIMARY KEY,
    job_title TEXT,
    question_text TEXT NOT NULL,
    category TEXT
);

CREATE TABLE IF NOT EXISTS interview_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(candidate_id),
    job_id UUID REFERENCES jobs(job_id),
    interviewer_id UUID REFERENCES interviewers(interviewer_id),
    stage_id INTEGER REFERENCES interview_stages(stage_id),
    interview_date TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'Scheduled'
);

CREATE TABLE IF NOT EXISTS interview_feedback (
    feedback_id SERIAL PRIMARY KEY,
    schedule_id UUID REFERENCES interview_schedules(schedule_id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    decision TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidate_responses (
    response_id SERIAL PRIMARY KEY,
    schedule_id UUID REFERENCES interview_schedules(schedule_id),
    question_id INTEGER REFERENCES questions_bank(question_id),
    answer_text TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS login_logs (
    log_id SERIAL PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(candidate_id),
    login_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE INDEX IF NOT EXISTS idx_candidate_education_candidate_id
ON candidate_education(candidate_id);

CREATE INDEX IF NOT EXISTS idx_candidate_audit_log_candidate_changed_at
ON candidate_audit_log(candidate_id, changed_at DESC);

CREATE INDEX IF NOT EXISTS idx_login_logs_candidate_timestamp
ON login_logs(candidate_id, login_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_interview_schedules_candidate_id
ON interview_schedules(candidate_id);

CREATE INDEX IF NOT EXISTS idx_interview_schedules_job_id
ON interview_schedules(job_id);

CREATE INDEX IF NOT EXISTS idx_interview_schedules_interviewer_id
ON interview_schedules(interviewer_id);

CREATE INDEX IF NOT EXISTS idx_interview_schedules_stage_id
ON interview_schedules(stage_id);

CREATE INDEX IF NOT EXISTS idx_interview_feedback_schedule_id
ON interview_feedback(schedule_id);

CREATE INDEX IF NOT EXISTS idx_interview_feedback_decision
ON interview_feedback(decision);

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
);

CREATE INDEX IF NOT EXISTS idx_agent_interactions_feedback
ON analytics.agent_interactions(was_helpful, created_at DESC);

CREATE TABLE IF NOT EXISTS analytics.genai_copilot_outputs (
    output_id SERIAL PRIMARY KEY,
    user_email TEXT,
    artifact_type TEXT NOT NULL,
    prompt_context JSONB,
    generated_content TEXT NOT NULL,
    guardrail_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_genai_copilot_outputs_created_at
ON analytics.genai_copilot_outputs(created_at DESC);

CREATE TABLE IF NOT EXISTS analytics.genai_agent_runs (
    run_id SERIAL PRIMARY KEY,
    user_email TEXT,
    run_type TEXT NOT NULL,
    prompt TEXT,
    agent_trace JSONB,
    final_answer TEXT,
    guardrail_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_genai_agent_runs_created_at
ON analytics.genai_agent_runs(created_at DESC);
