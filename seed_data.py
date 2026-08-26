import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("config/.env")

def seed():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            port=os.environ.get("DB_PORT")
        )
        cur = conn.cursor()

        jobs = [
            ('Data Engineer', 'Data Platform', '80k - 120k', 'Bangalore'),
            ('Data Scientist', 'AI/ML', '90k - 140k', 'Remote'),
            ('ML Engineer', 'AI/ML', '100k - 150k', 'Bangalore'),
            ('Data Analyst', 'Business Intelligence', '60k - 90k', 'Hyderabad')
        ]
        cur.executemany("INSERT INTO jobs (job_title, department, salary_range, job_location) VALUES (%s, %s, %s, %s)", jobs)

        interviewers = [
            ('Gaurav Lathiya', 'gaurav@altimetrik.com', 'Data Engineering'),
            ('Vignesh N', 'vignesh@altimetrik.com', 'Data Science'),
            ('Sarah Smith', 'sarah@altimetrik.com', 'HR Management')
        ]
        cur.executemany("INSERT INTO interviewers (full_name, email, specialization) VALUES (%s, %s, %s)", interviewers)

        stages = [('Screening',), ('Technical Round 1',), ('Technical Round 2',), ('Managerial Round',), ('HR Round',)]
        cur.executemany("INSERT INTO interview_stages (stage_name) VALUES (%s)", stages)

        conn.commit()
        print("✅ Ecosystem Seeded! Jobs, Interviewers, and Stages are now live in Azure.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Seeding Failed: {e}")

if __name__ == "__main__":
    seed()
