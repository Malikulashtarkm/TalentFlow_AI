import os
import random
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
from faker import Faker

load_dotenv("config/.env")
fake = Faker('en_IN')

def fill_gaps():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            port=os.environ.get("DB_PORT")
        )
        cur = conn.cursor()
        print("🔍 Checking for empty tables...")

        # --- 1. FILL RECRUITERS ---
        cur.execute("SELECT count(*) FROM recruiters")
        if cur.fetchone()[0] == 0:
            print("Adding Recruiters...")
            recruiter_names = ["Priya Sharma", "Amit Khanna", "Sonia Varma", "Vikram Seth", "Anjali Gupta"]
            recruiters = [(name, f"{name.lower().replace(' ', '.')}@altimetrik.com", random.choice(['North', 'South', 'East', 'West'])) for name in recruiter_names]
            cur.executemany("INSERT INTO recruiters (full_name, email, region) VALUES (%s, %s, %s)", recruiters)
        else:
            print("✅ Recruiters already present.")

        # --- 2. FILL QUESTIONS BANK ---
        cur.execute("SELECT count(*) FROM questions_bank")
        if cur.fetchone()[0] == 0:
            print("Adding Question Bank...")
            # Logic: Different questions for different roles
            bank = [
                ('Data Engineer', 'Explain the difference between a Data Lake and a Data Warehouse.', 'Architecture'),
                ('Data Engineer', 'How do you handle late-arriving dimensions in an SCD Type 2 pipeline?', 'ETL'),
                ('Data Engineer', 'What is the difference between a Clustered and Non-Clustered index?', 'SQL'),
                ('Data Scientist', 'Explain the bias-variance tradeoff in machine learning.', 'ML Theory'),
                ('Data Scientist', 'How does a Random Forest differ from Gradient Boosting?', 'ML Algorithms'),
                ('Data Scientist', 'What is the purpose of a ROC curve in binary classification?', 'Evaluation'),
                ('ML Engineer', 'How do you handle vanishing gradients in deep neural networks?', 'Deep Learning'),
                ('ML Engineer', 'What is the difference between Batch and Online inference?', 'MLOps'),
                ('Data Analyst', 'How do you handle missing values in a large dataset?', 'Data Cleaning'),
                ('Data Analyst', 'Explain the difference between a LEFT JOIN and an INNER JOIN.', 'SQL'),
            ]
            cur.executemany("INSERT INTO questions_bank (job_title, question_text, category) VALUES (%s, %s, %s)", bank)
        else:
            print("✅ Question Bank already present.")

        # --- 3. FILL CANDIDATE RESPONSES ---
        # We link these to 'Completed' interviews to make it realistic
        cur.execute("SELECT count(*) FROM candidate_responses")
        if cur.fetchone()[0] == 0:
            print("Adding Candidate Responses...")
            # Get all completed schedules and all questions
            cur.execute("SELECT schedule_id FROM interview_feedback")
            schedule_ids = [r[0] for r in cur.fetchall()]
            cur.execute("SELECT question_id FROM questions_bank")
            q_ids = [r[0] for r in cur.fetchall()]

            responses = []
            for s_id in schedule_ids:
                # Each completed interview gets 2-3 random questions answered
                for _ in range(random.randint(2, 4)):
                    responses.append((s_id, random.choice(q_ids), fake.paragraph(nb_sentences=3)))
            
            cur.executemany("INSERT INTO candidate_responses (schedule_id, question_id, answer_text) VALUES (%s, %s, %s)", responses)
        else:
            print("✅ Candidate Responses already present.")

        conn.commit()
        print("\n✅ ALL GAPS FILLED! Your database is now 100% complete.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Filling failed: {e}")

if __name__ == "__main__":
    fill_gaps()