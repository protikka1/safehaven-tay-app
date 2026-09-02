import unittest
import sqlite3
import os

class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        # Locate the database (checks workspace/scratch or current folder)
        self.db_path = "recovery-app.db"
        if not os.path.exists(self.db_path):
            # If not in root, try fallback location
            self.db_path = "../recovery-app.db"
            
    def test_database_exists(self):
        """Verify the database file exists."""
        self.assertTrue(os.path.exists(self.db_path), f"Database file not found at {self.db_path}")

    def test_core_tables_exist(self):
        """Verify that all core tables are present in the schema."""
        expected_tables = {
            "youth_profiles",
            "caseworkers",
            "clinicians",
            "assessments",
            "care_assignments",
            "mat_prescriptions",
            "facilities"
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        for table in expected_tables:
            self.assertIn(table, tables, f"Mandatory table '{table}' is missing from the database schema.")

    def test_clinician_npi_constraint(self):
        """Verify that clinicians table contains the NPI column."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(clinicians);")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        self.assertIn("npi_number", columns, "The 'npi_number' column is missing from the clinicians table.")

if __name__ == '__main__':
    unittest.main()
