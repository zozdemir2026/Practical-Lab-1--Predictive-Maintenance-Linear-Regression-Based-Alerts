
# Database Connection: Creates a database service to connect the application to the Neon database.

from multiprocessing import connection
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv


class DatabaseService:

    def __init__(self):
        load_dotenv()
        self.database_url = os.getenv("DATABASE_URL")

    def connect(self):
        connection = psycopg2.connect(self.database_url)
        return connection

    def insert_record(self, data_point):
        connection = self.connect()
        cursor = connection.cursor()

        insert_sql = """
        INSERT INTO robot_measurements (
            trait, axis_1, axis_2, axis_3, axis_4,
            axis_5, axis_6, axis_7, axis_8, recorded_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        record = data_point.iloc[0] 
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
                record["Time"]
            )
        cursor.execute(insert_sql, values)
        connection.commit()
        cursor.close()
        connection.close()

    def read_data(self):        
        connection = self.connect()
        query = """
        SELECT *
        FROM robot_measurements
        ORDER BY recorded_at ASC
    """

        df = pd.read_sql_query(query, connection)

        connection.close()

        return df