from pathlib import Path
from dotenv import load_dotenv
import os


class Initialization:

    def __init__(self):
        # Load variables from .env
        load_dotenv()

        # Project root folder
        self.project_root = Path(__file__).resolve().parent.parent

        # CSV file path
        self.data_path = (
            self.project_root
            / "data"
            / "raw"
            / "RMBR4-2_export_test.csv"
        )

        # Database connection string
        self.database_url = os.getenv("DATABASE_URL")

    def get_data_path(self):
        return self.data_path

    def get_database_url(self):
        return self.database_url