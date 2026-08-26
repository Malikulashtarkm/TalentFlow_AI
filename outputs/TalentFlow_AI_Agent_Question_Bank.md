# TalentFlow AI Agent Question Bank

Use these questions in the **Ask Data** tab of the admin portal.

Recommended demo mode:

```env
LOCAL_AGENT_SPEED_MODE=fast
LOCAL_ALLOW_SLOW_LLM=false
```

This keeps the agent quick and avoids long Hugging Face inference during presentation.

## Best Fast Demo Questions

These are the safest questions to use in a live demo.

### Hiring Overview

1. Give me a hiring summary.
2. Show the current hiring pipeline overview.
3. What is the overall recruitment status?
4. Give me the main hiring KPIs.
5. Show total candidates, roles, interviews, feedback, and hire recommendations.

### Interviewer Assignments

1. Who is the interviewer interviewing?
2. Which candidate is each interviewer interviewing?
3. Show interviewer candidate assignments.
4. Who are interviewers assigned to interview?
5. List interviewers and their candidates.
6. Show interview schedules with candidate, interviewer, job, stage, and status.
7. Which interviews are currently scheduled?
8. Show upcoming interviews.

### Candidate Pipeline

1. Which cities have the most candidates?
2. Which cities have the strongest candidate pipeline?
3. Best city for talent pipeline.
4. Compare candidates, interviews, and hires by city.
5. Show candidate count by city.
6. Show candidate location distribution.

### Candidate Quality

1. Show highest rated candidates.
2. Which candidates have the best interview ratings?
3. Show top candidates by average rating.
4. Which candidates have high ratings but were not hired?
5. Show strong candidates who did not get a hire decision.
6. Candidates with good interview feedback but hold or reject decision.

### Job And Hiring Decisions

1. What is the hire rate by job?
2. Which jobs have the best hire rate?
3. Show hire, hold, and reject decisions by job.
4. Which jobs have the most hire recommendations?
5. Compare feedback decisions across jobs.
6. Show total feedback and hire count for each role.

### Interviewer Workload

1. Which interviewers have pending feedback?
2. Show interviewer workload.
3. Which interviewers have the highest pending feedback workload?
4. Show assigned interviews and completed feedback by interviewer.
5. Which interviewers need to submit feedback?

### Candidate Engagement

1. Show candidate engagement by login count.
2. Which candidates have logged in the most?
3. Which active candidates have not logged in recently?
4. Candidates with no recent login.
5. Show candidates who are inactive for 30 days.
6. Show latest login by candidate.

### Education And Performance

1. Show education profile.
2. Which degrees have the most candidates?
3. Which degrees are associated with better ratings?
4. Compare education degree with interview performance.
5. Best performing degrees by average rating.
6. Show average GPA by degree.
7. Show average expected salary by degree.

### Pipeline Bottlenecks

1. Where is the hiring pipeline stuck?
2. Show bottlenecks by stage and status.
3. Which interview stages have most pending candidates?
4. Show interview count by stage and status.
5. Which stage has the most scheduled interviews?

### Profile Changes And Audit

1. Show profile changes.
2. Show candidate audit history.
3. Which candidate profiles were changed recently?
4. Show changed fields for candidates.
5. Show recent candidate updates.

### Question Bank

1. Do we have enough interview questions by role?
2. Show question bank coverage by job title and category.
3. Question coverage for each role.
4. Which roles have the most interview questions?
5. Show interview questions by category.

### ML Insights

1. What are the top ML feature insights?
2. Show ML feature importance.
3. Which features influence model predictions the most?
4. Show model feature ranks.
5. What are the top predictive features?

## Good Follow-Up Questions For Demo Explanation

Use these after the table/chart appears. Some may need rephrasing or corrected SQL if the local agent has not learned the exact wording.

1. Why are these candidates important?
2. Which result should the recruiter act on first?
3. Which city should we focus hiring efforts on?
4. Which interviewer has the most pending work?
5. Which job role looks healthiest?
6. Which stage is slowing down the process?
7. Which education background seems strongest?
8. Which candidates should be followed up with?

## Advanced Questions If Slow Hugging Face Fallback Is Enabled

Only use these if you set:

```env
LOCAL_ALLOW_SLOW_LLM=true
```

These can be slower because they may use the local Hugging Face model.

1. Which candidates from a specific city have strong ratings but no hire decision?
2. Which interviewers specialize in roles where candidates are getting rejected?
3. Which jobs have many interviews but low hire recommendations?
4. Which candidates have high GPA, high rating, and high engagement?
5. Which cities have many candidates but low interview conversion?
6. Which roles need more question bank coverage?
7. Which interviewers are overloaded compared with others?
8. Which candidates changed their profile after being scheduled?
9. Which candidates have interview feedback but no recent login?
10. Which stages have high completion but low hire decisions?

## Custom SQL Examples

The agent also accepts read-only `SELECT` or `WITH` SQL. It blocks write operations and sensitive fields.

### Show all jobs

```sql
SELECT job_title, department, salary_range, job_location
FROM jobs
ORDER BY job_title
```

### Show scheduled interviews

```sql
SELECT
    i.full_name AS interviewer,
    c.first_name || ' ' || c.last_name AS candidate,
    j.job_title,
    s.interview_date,
    s.status
FROM interview_schedules s
JOIN interviewers i ON i.interviewer_id = s.interviewer_id
JOIN candidates c ON c.candidate_id = s.candidate_id
JOIN jobs j ON j.job_id = s.job_id
ORDER BY s.interview_date DESC
```

### Show feedback by candidate

```sql
SELECT
    c.first_name || ' ' || c.last_name AS candidate,
    j.job_title,
    f.rating,
    f.decision,
    f.submitted_at
FROM interview_feedback f
JOIN interview_schedules s ON s.schedule_id = f.schedule_id
JOIN candidates c ON c.candidate_id = s.candidate_id
JOIN jobs j ON j.job_id = s.job_id
ORDER BY f.submitted_at DESC
```

### Show login activity

```sql
SELECT
    c.first_name || ' ' || c.last_name AS candidate,
    COUNT(l.log_id) AS login_count,
    MAX(l.login_timestamp) AS latest_login
FROM candidates c
LEFT JOIN login_logs l ON l.candidate_id = c.candidate_id
GROUP BY c.candidate_id, c.first_name, c.last_name
ORDER BY login_count DESC, latest_login DESC NULLS LAST
```

## Questions To Avoid In Fast Demo Mode

Avoid these unless you provide custom SQL or enable slow fallback:

1. Very broad questions like "Analyze everything."
2. Questions requiring external internet data.
3. Questions asking for passwords, secrets, or private credentials.
4. Questions asking the agent to update, delete, or insert records.
5. Long multi-part questions that need several separate queries.
6. Questions using table names or fields that do not exist in the schema.

## Best Final Demo Sequence

1. Give me a hiring summary.
2. Who is the interviewer interviewing?
3. Which interviewers have pending feedback?
4. Which candidates have high ratings but were not hired?
5. Which cities have the strongest candidate pipeline?
6. Which degrees are associated with better ratings?
7. Where is the hiring pipeline stuck?
8. What are the top ML feature insights?

This sequence demonstrates operational data, scheduling, feedback, analytics, engagement, education, bottleneck analysis, and ML explainability.
