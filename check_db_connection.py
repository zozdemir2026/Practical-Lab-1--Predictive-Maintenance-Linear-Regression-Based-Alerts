## Database Connection Test
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL was not found in the .env file.")

connection = psycopg2.connect(database_url)
connection.close()

print("Database connection successful!")