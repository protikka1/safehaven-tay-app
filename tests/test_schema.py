import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "recovery_app.db"


class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        self.db_path = DB_PATH

    def test_database_exists(self):
        """Verify the synthetic test database exists."""
        self.assertTrue(
            self.db_path.exists(),
            f"Database file not found at {self.db_path}",
        )

    def test_core_tables_exist(self):
        """Verify that all core tables are present in the schema."""
        expected_tables = {
            "youth_profiles",
            "caseworkers",
            "clinicians",
            "assessments",
            "care_assignments",
            "mat_prescriptions",
            "facilities",
        }

        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        tables = {row[0] for row in rows}

        for table in expected_tables:
            self.assertIn(
                table,
                tables,
                f"Mandatory table '{table}' is missing from the database schema.",
            )

    def test_clinician_npi_constraint(self):
        """Verify that the clinicians table contains the NPI column."""
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute("PRAGMA table_info(clinicians);").fetchall()
        columns = [row[1] for row in rows]
        self.assertIn(
            "npi_number",
            columns,
            "The 'npi_number' column is missing from the clinicians table.",
        )


if __name__ == "__main__":
    unittest.main()
