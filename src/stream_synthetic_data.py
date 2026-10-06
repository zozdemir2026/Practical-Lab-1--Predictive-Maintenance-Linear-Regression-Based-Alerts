import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")

connection = psycopg2.connect(DATABASE_URL)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS synthetic_stream (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMPTZ,
    time_seconds DOUBLE PRECISION,
    trait TEXT,

    axis_1 DOUBLE PRECISION,
    axis_2 DOUBLE PRECISION,
    axis_3 DOUBLE PRECISION,
    axis_4 DOUBLE PRECISION,
    axis_5 DOUBLE PRECISION,
    axis_6 DOUBLE PRECISION,
    axis_7 DOUBLE PRECISION,
    axis_8 DOUBLE PRECISION
);
""")

connection.commit()

cursor.close()
connection.close()

print("synthetic_stream table created successfully.")

import time
import pandas as pd

csv_path = PROJECT_ROOT / "data" / "generated" / "synthetic_test.csv"

stream_df = pd.read_csv(csv_path)

connection = psycopg2.connect(DATABASE_URL)
cursor = connection.cursor()

# Clear previous test stream so rerunning does not create duplicates
cursor.execute("DELETE FROM synthetic_stream;")
connection.commit()

for index, row in stream_df.iterrows():

    cursor.execute("""
        INSERT INTO synthetic_stream (
            recorded_at,
            time_seconds,
            trait,
            axis_1,
            axis_2,
            axis_3,
            axis_4,
            axis_5,
            axis_6,
            axis_7,
            axis_8
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row["recorded_at"],
        row["time_seconds"],
        row["trait"],
        row["axis_1"],
        row["axis_2"],
        row["axis_3"],
        row["axis_4"],
        row["axis_5"],
        row["axis_6"],
        row["axis_7"],
        row["axis_8"]
    ))

    connection.commit()

    # Accelerated time-based streaming simulation
    time.sleep(0.05)

    if (index + 1) % 50 == 0:
        print(f"Streamed {index + 1} / {len(stream_df)} rows")

cursor.close()
connection.close()

print("Synthetic streaming completed successfully.")