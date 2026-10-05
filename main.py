import os
import time
import pandas as pd
import psycopg2
from dotenv import load_dotenv

## Step 1: Load the CSV into Pandas
class DataCollection:
    def load_csv(self, file_path):
        return pd.read_csv(file_path)

collection = DataCollection()
data = collection.load_csv('data/raw/RMBR4-2_export_test.csv')

## Inspect and Clean Dataset
columns_to_keep = [
    "Trait",
    "Axis #1", "Axis #2", "Axis #3", "Axis #4",
    "Axis #5", "Axis #6", "Axis #7", "Axis #8",
    "Time"
]

data = data[columns_to_keep].copy()
data["Time"] = pd.to_datetime(data["Time"], utc=True)

## Select the First Record
record = data.iloc[0]

## Connect to Neon Database
load_dotenv()
connection = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = connection.cursor()

## Ensure Table Exists First
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

## Prepare and Insert One Record
insert_sql = """
INSERT INTO robot_measurements (
    trait, axis_1, axis_2, axis_3, axis_4,
    axis_5, axis_6, axis_7, axis_8, recorded_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

values = (
    str(record["Trait"]),
    float(record["Axis #1"]),
    float(record["Axis #2"]),
    float(record["Axis #3"]),
    float(record["Axis #4"]),
    float(record["Axis #5"]),
    float(record["Axis #6"]),
    float(record["Axis #7"]),
    float(record["Axis #8"]),
    record["Time"].to_pydatetime()
)

cursor.execute(insert_sql, values)
connection.commit()

print("Connected and first record saved successfully!")

## Clean up
cursor.close()
connection.close()