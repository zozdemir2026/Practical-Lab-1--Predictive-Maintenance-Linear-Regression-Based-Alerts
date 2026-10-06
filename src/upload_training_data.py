import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv


# -----------------------------
# 1. Find project folders
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

csv_path = PROJECT_ROOT / "data" / "raw" / "RMBR4-2_export_test.csv"
env_path = PROJECT_ROOT / ".env"


# -----------------------------
# 2. Load environment variables
# -----------------------------
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env")


# -----------------------------
# 3. Read training CSV
# -----------------------------
data = pd.read_csv(csv_path)

columns_to_keep = [
    "Trait",
    "Axis #1",
    "Axis #2",
    "Axis #3",
    "Axis #4",
    "Axis #5",
    "Axis #6",
    "Axis #7",
    "Axis #8",
    "Time"
]

data = data[columns_to_keep].copy()

data["Time"] = pd.to_datetime(
    data["Time"],
    utc=True
)

print("Training rows:", len(data))


# -----------------------------
# 4. Connect to Neon
# -----------------------------
connection = psycopg2.connect(DATABASE_URL)
cursor = connection.cursor()

print("Connected to Neon")


# -----------------------------
# 5. Create table
# -----------------------------
create_table_sql = """
CREATE TABLE IF NOT EXISTS robot_measurements (
    id SERIAL PRIMARY KEY,
    trait VARCHAR(255),
    axis_1 DOUBLE PRECISION,
    axis_2 DOUBLE PRECISION,
    axis_3 DOUBLE PRECISION,
    axis_4 DOUBLE PRECISION,
    axis_5 DOUBLE PRECISION,
    axis_6 DOUBLE PRECISION,
    axis_7 DOUBLE PRECISION,
    axis_8 DOUBLE PRECISION,
    recorded_at TIMESTAMPTZ
);
"""

cursor.execute(create_table_sql)


# -----------------------------
# 6. Remove old training rows
# -----------------------------
cursor.execute(
    "TRUNCATE TABLE robot_measurements RESTART IDENTITY;"
)


# -----------------------------
# 7. Insert ALL CSV rows
# -----------------------------
insert_sql = """
INSERT INTO robot_measurements (
    trait,
    axis_1,
    axis_2,
    axis_3,
    axis_4,
    axis_5,
    axis_6,
    axis_7,
    axis_8,
    recorded_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""


for _, row in data.iterrows():

    values = (
        str(row["Trait"]),
        float(row["Axis #1"]),
        float(row["Axis #2"]),
        float(row["Axis #3"]),
        float(row["Axis #4"]),
        float(row["Axis #5"]),
        float(row["Axis #6"]),
        float(row["Axis #7"]),
        float(row["Axis #8"]),
        row["Time"].to_pydatetime()
    )

    cursor.execute(insert_sql, values)


# -----------------------------
# 8. Save changes
# -----------------------------
connection.commit()

print(f"Successfully uploaded {len(data)} rows to Neon.")


# -----------------------------
# 9. Close connection
# -----------------------------
cursor.close()
connection.close()

print("Database connection closed.")