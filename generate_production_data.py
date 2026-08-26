import os
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
from faker import Faker

load_dotenv("config/.env")
fake = Faker('en_IN')


DEMO_RESET_FLAG = "ALLOW_DEMO_DATA_RESET"


def require_demo_reset_enabled():
    """Prevent accidental truncation of a real database."""
    if os.environ.get(DEMO_RESET_FLAG, "").lower() not in {"1", "true", "yes"}:
        raise RuntimeError(
            f"Refusing to reset data. Set {DEMO_RESET_FLAG}=true only for demo databases."
        )


def profile_from_cluster(cluster):
    if cluster == 'high_flyer':
        return {
            "experience": random.randint(6, 15),
            "current_salary": random.randint(120000, 200000),
            "expected_salary": random.randint(155000, 245000),
            "login_count": random.randint(18, 42),
            "degree": random.choice(['M.Tech', 'PhD', 'B.Tech']),
            "gpa": round(random.uniform(3.45, 4.0), 2),
        }
    if cluster == 'entry_level':
        return {
            "experience": random.randint(0, 3),
            "current_salary": random.randint(30000, 65000),
            "expected_salary": random.randint(45000, 95000),
            "login_count": random.randint(6, 18),
            "degree": random.choice(['B.Tech', 'B.Sc', 'M.Tech']),
            "gpa": round(random.uniform(2.8, 3.7), 2),
        }
    return {
        "experience": random.randint(1, 10),
        "current_salary": random.randint(45000, 110000),
        "expected_salary": random.randint(70000, 135000),
        "login_count": random.randint(1, 5),
        "degree": random.choice(['B.Tech', 'B.Sc']),
        "gpa": round(random.uniform(2.2, 3.2), 2),
    }


def interview_signal(profile, stage_id, salary_range):
    """Create learnable labels for ML instead of random interview outcomes."""
    score = 0
    score += min(profile["experience"], 10) * 4
    score += profile["login_count"] * 1.4
    score += profile["gpa"] * 14
    score += 12 if profile["degree"] in {"M.Tech", "PhD"} else 5
    score += min(stage_id, 5) * 4

    upper_salary = int(salary_range.split("-")[-1].replace(",", "").strip())
    if profile["expected_salary"] <= upper_salary:
        score += 12
    elif profile["expected_salary"] > upper_salary * 1.25:
        score -= 15

    score += random.uniform(-12, 12)
    rating = max(1, min(5, round(score / 24)))
    if score >= 92:
        decision = "Hire"
    elif score >= 68:
        decision = "Hold"
    else:
        decision = "Reject"
    return rating, decision


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        port=os.environ.get("DB_PORT")
    )

def seed_enterprise_data():
    try:
        require_demo_reset_enabled()
        conn = get_connection()
        cur = conn.cursor()
        print("🚀 Starting High-Volume Production Data Simulation...")

        all_tables = [
            "candidate_responses", "interview_feedback", "interview_schedules", 
            "candidate_education", "login_logs", "candidates", "questions_bank",
            "jobs", "recruiters", "interviewers", "interview_stages"
        ]
        
        tables_string = ", ".join(all_tables)
        print(f"🧹 Clearing existing data from: {tables_string}...")
        cur.execute(f"TRUNCATE TABLE {tables_string} CASCADE;")

        jobs_data = [
            ('Data Engineer', 'Data Platform', '80,000 - 120,000', 'Bangalore'),
            ('Data Scientist', 'AI/ML', '90,000 - 140,000', 'Remote'),
            ('ML Engineer', 'AI/ML', '100,000 - 150,000', 'Bangalore'),
            ('Data Analyst', 'Business Intelligence', '60,000 - 90,000', 'Hyderabad'),
            ('Backend Developer', 'Product', '70,000 - 110,000', 'Pune'),
            ('Cloud Architect', 'Infrastructure', '120,000 - 180,000', 'Bangalore')
        ]
        cur.executemany("INSERT INTO jobs (job_title, department, salary_range, job_location) VALUES (%s, %s, %s, %s)", jobs_data)
        cur.execute("SELECT job_id, salary_range FROM jobs")
        job_salary_map = {str(row[0]): row[1] for row in cur.fetchall()}

        stages_data = [('Screening',), ('Technical Round 1',), ('Technical Round 2',), ('Managerial Round',), ('HR Round',)]
        cur.executemany("INSERT INTO interview_stages (stage_name) VALUES (%s)", stages_data)

        print("👥 Generating 15 Interviewers...")
        interviewer_names = [
            "Gaurav Lathiya", "Vignesh N", "Sarah Smith", "Amit Sharma", "Priya Patel", 
            "Rahul Verma", "Sonia Gupta", "Vikram Singh", "Ananya Rao", "Karan Malhotra",
            "Deepika Padukone", "Rohan Joshi", "Sneha Reddy", "Arjun Kapoor", "Meera Nair"
        ]
        specs = ["Data Engineering", "Data Science", "HR Management", "Cloud Architecture", "Backend Systems"]
        
        interviewers = []
        for name in interviewer_names:
            email = name.lower().replace(" ", ".") + "@altimetrik.com"
            interviewers.append((name, email, random.choice(specs)))
        
        cur.executemany("INSERT INTO interviewers (full_name, email, specialization) VALUES (%s, %s, %s)", interviewers)

        print("👥 Generating 600+ candidates with behavioral clusters...")
        candidates = []
        education_records = []
        candidate_profiles = {}
        
        for _ in range(620):
            c_id = fake.uuid4()
            email = fake.unique.email()
            
            cluster = random.choice(['high_flyer', 'entry_level', 'ghost'])
            profile = profile_from_cluster(cluster)
            candidate_profiles[str(c_id)] = profile

            candidates.append((
                c_id, email, "Pass123!", fake.first_name(), fake.last_name(),
                fake.phone_number(), fake.city(), fake.state(), "India", profile["expected_salary"]
            ))

            education_records.append((
                c_id, profile["degree"],
                fake.company() + " University", random.randint(2010, 2024), profile["gpa"]
            ))

        cur.executemany("""
            INSERT INTO candidates (candidate_id, email, password, first_name, last_name, phone_number, city, state, country, expected_salary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, candidates)
        
        cur.executemany("""
            INSERT INTO candidate_education (candidate_id, degree, university, passing_year, gpa) 
            VALUES (%s, %s, %s, %s, %s)
        """, education_records)

        print("📅 Scheduling ~1,500 interviews...")
        cur.execute("SELECT candidate_id FROM candidates")
        c_ids = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT job_id FROM jobs")
        j_ids = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT interviewer_id FROM interviewers")
        i_ids = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT stage_id FROM interview_stages")
        s_ids = [r[0] for r in cur.fetchall()]

        schedules = []
        for c_id in c_ids:
            num_interviews = random.choice([0, 1, 2, 3, 4]) 
            current_stage_idx = 0
            for _ in range(num_interviews):
                status = 'Completed' if current_stage_idx < 2 else random.choice(['Completed', 'Scheduled', 'Cancelled'])
                date = datetime.now() - timedelta(days=random.randint(0, 60))
                selected_job = random.choice(j_ids)
                schedules.append((
                    fake.uuid4(), c_id, selected_job,
                    random.choice(i_ids), s_ids[current_stage_idx], date, status
                ))
                current_stage_idx += 1
                if current_stage_idx >= len(s_ids): break
        
        cur.executemany("""
            INSERT INTO interview_schedules (schedule_id, candidate_id, job_id, interviewer_id, stage_id, interview_date, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, schedules)

        print("📝 Adding Feedback for completed interviews...")
        cur.execute("""
            SELECT schedule_id, candidate_id, job_id, stage_id
            FROM interview_schedules
            WHERE status = 'Completed'
        """)
        completed_schedules = cur.fetchall()
        
        feedback = []
        for s_id, c_id, job_id, stage_id in completed_schedules:
            rating, decision = interview_signal(
                candidate_profiles[str(c_id)],
                stage_id,
                job_salary_map[str(job_id)],
            )
            feedback.append((
                s_id,
                rating,
                fake.sentence(nb_words=15),
                decision
            ))
        cur.executemany("INSERT INTO interview_feedback (schedule_id, rating, comments, decision) VALUES (%s, %s, %s, %s)", feedback)

        print("🔑 Simulating thousands of login events...")
        logs = []
        for c_id in c_ids:
            num_logins = candidate_profiles[str(c_id)]["login_count"]
            for _ in range(num_logins):
                log_date = datetime.now() - timedelta(days=random.randint(0, 90))
                logs.append((c_id, log_date))
        
        cur.executemany("INSERT INTO login_logs (candidate_id, login_timestamp) VALUES (%s, %s)", logs)

        conn.commit()
        print(f"\n✅ SUCCESS! Enterprise-scale data seeded.")
        print(f"Candidates: {len(candidates)} | Interviews: {len(schedules)} | Login Events: {len(logs)}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Seeding Failed: {e}")

if __name__ == "__main__":
    seed_enterprise_data()
