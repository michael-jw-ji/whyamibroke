import psycopg2
import os

# Use the environment variable that you confirmed is correct
DB_URL = os.environ.get('DATABASE_URL')

# psycopq2 uses a different connection string format by default, so we'll 
# extract the key details for the direct connect call:
try:
    conn = psycopg2.connect(
        host="localhost",
        database="expenses",
        user="postgres",
        password="app_password",
        port="5432"
    )
    print("SUCCESS: Connection established!")
    conn.close()
except Exception as e:
    print(f"ERROR: Connection failed. Details: {e}")

exit()