import os
from dotenv import load_dotenv
from supabase import create_client

# 1. Load the secrets from the /config/.env file
load_dotenv("config/.env")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"Checking URL: {url}")
print(f"Checking Key: {key[:5]}...") # Only print first 5 chars for security

if url and key:
    try:
        # 2. Try to connect to the database
        supabase = create_client(url, key)
        print("✅ Connection Successful! Your secret handshake works.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
else:
    print("❌ Error: Could not find URL or Key in the .env file.")