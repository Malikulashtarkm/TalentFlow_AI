import os
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
from faker import Faker

load_dotenv("config/.env")
fake = Faker('en_IN')

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
        conn = get_connection()
        cur = conn.cursor()
        print("🚀 Starting High-Volume Production Data Simulation...")

        # --- 1. CLEANUP (The "Nuclear" Option) ---
        # We list EVERY table in the system and use CASCADE to ignore foreign key constraints
        all_tables = [
            "candidate_responses", "interview_feedback", "interview_schedules", 
            "candidate_education", "login_logs", "candidates", "questions_bank",
            "jobs", "recruiters", "interviewers", "interview_stages"
        ]
        
        # Join the list into a single string: "table1, table2, table3..."
        tables_string = ", ".join(all_tables)
        print(f"🧹 Clearing existing data from: {tables_string}...")
        cur.execute(f"TRUNCATE TABLE {tables_string} CASCADE;")

        # --- 2. REFERENCE DATA ---
        jobs_data = [
            ('Data Engineer', 'Data Platform', '80,000 - 120,000', 'Bangalore'),
            ('Data Scientist', 'AI/ML', '90,000 - 140,000', 'Remote'),
            ('ML Engineer', 'AI/ML', '100,000 - 150,000', 'Bangalore'),
            ('Data Analyst', 'Business Intelligence', '60,000 - 90,000', 'Hyderabad'),
            ('Backend Developer', 'Product', '70,000 - 110,000', 'Pune'),
            ('Cloud Architect', 'Infrastructure', '120,000 - 180,000', 'Bangalore')
        ]
        cur.executemany("INSERT INTO jobs (job_title, department, salary_range, job_location) VALUES (%s, %s, %s, %s)", jobs_data)

        stages_data = [('Screening',), ('Technical Round 1',), ('Technical Round 2',), ('Managerial Round',), ('HR Round',)]
        cur.executemany("INSERT INTO interview_stages (stage_name) VALUES (%s)", stages_data)

        # --- 3. INTERVIEWERS (15 Professionals) ---
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

        # --- 4. CANDIDATES (600+ Records) ---
        print("👥 Generating 600+ candidates with behavioral clusters...")
        candidates = []
        education_records = []
        
        for _ in range(620):
            c_id = fake.uuid4()
            email = fake.unique.email()
            
            cluster = random.choice(['high_flyer', 'entry_level', 'ghost'])
            
            if cluster == 'high_flyer':
                exp = random.randint(6, 15)
                curr_sal = random.randint(120000, 200000)
                exp_sal = curr_sal + random.randint(20000, 50000)
                login_count = random.randint(15, 40)
            elif cluster == 'entry_level':
                exp = random.randint(0, 3)
                curr_sal = random.randint(30000, 60000)
                exp_sal = curr_sal + random.randint(10000, 30000)
                login_count = random.randint(5, 15)
            else: # Ghost candidates
                exp = random.randint(1, 10)
                curr_sal = random.randint(40000, 100000)
                exp_sal = curr_sal + 10000
                login_count = random.randint(1, 3)

            candidates.append((
                c_id, email, "Pass123!", fake.first_name(), fake.last_name(), 
                fake.phone_number(), fake.city(), fake.state(), "India"
            ))

            education_records.append((
                c_id, random.choice(['B.Tech', 'M.Tech', 'B.Sc', 'PhD']), 
                fake.company() + " University", random.randint(2010, 2024), round(random.uniform(3.0, 4.0), 2)
            ))

        cur.executemany("""
            INSERT INTO candidates (candidate_id, email, password, first_name, last_name, phone_number, city, state, country) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, candidates)
        
        cur.executemany("""
            INSERT INTO candidate_education (candidate_id, degree, university, passing_year, gpa) 
            VALUES (%s, %s, %s, %s, %s)
        """, education_records)

        # --- 5. INTERVIEW SCHEDULES ---
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
                schedules.append((
                    fake.uuid4(), c_id, random.choice(j_ids), 
                    random.choice(i_ids), s_ids[current_stage_idx], date, status
                ))
                current_stage_idx += 1
                if current_stage_idx >= len(s_ids): break
        
        cur.executemany("""
            INSERT INTO interview_schedules (schedule_id, candidate_id, job_id, interviewer_id, stage_id, interview_date, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, schedules)

        # --- 6. INTERVIEW FEEDBACK ---
        print("📝 Adding Feedback for completed interviews...")
        cur.execute("SELECT schedule_id FROM interview_schedules WHERE status = 'Completed'")
        completed_schedules = [r[0] for r in cur.fetchall()]
        
        feedback = []
        for s_id in completed_schedules:
            feedback.append((
                s_id, random.randint(1, 5), 
                fake.sentence(nb_words=15), random.choice(['Hire', 'Hold', 'Reject'])
            ))
        cur.executemany("INSERT INTO interview_feedback (schedule_id, rating, comments, decision) VALUES (%s, %s, %s, %s)", feedback)

        # --- 7. LOGIN LOGS ---
        print("🔑 Simulating thousands of login events...")
        logs = []
        for c_id in c_ids:
            # Using the logic from the loop above (roughly)
            num_logins = random.randint(1, 30)
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