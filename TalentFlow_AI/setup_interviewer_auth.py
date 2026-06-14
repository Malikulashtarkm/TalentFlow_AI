import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("config/.env")

def setup_auth():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            port=os.environ.get("DB_PORT")
        )
        cur = conn.cursor()

        # 1. Get all interviewers from the interviewers table
        cur.execute("SELECT full_name, email FROM interviewers")
        interviewers = cur.fetchall()

        default_password = "Password123!" # We will use this for all interviewers

        for name, email in interviewers:
            # Split name to get first_name and last_name
            name_parts = name.split(" ", 1)
            f_name = name_parts[0]
            l_name = name_parts[1] if len(name_parts) > 1 else ""

            # 2. Insert them into the candidates table so they can login
            # We use 'ON CONFLICT' so if they are already there, it doesn't crash
            cur.execute("""
                INSERT INTO candidates (email, password, first_name, last_name) 
                VALUES (%s, %s, %s, %s) 
                ON CONFLICT (email) DO UPDATE SET password = EXCLUDED.password
            """, (email, default_password, f_name, l_name))
            
        conn.commit()
        print(f"✅ Interviewer Auth Setup Complete!")
        print(f"All interviewers can now log in with password: {default_password}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Setup Failed: {e}")

if __name__ == "__main__":
    setup_auth()