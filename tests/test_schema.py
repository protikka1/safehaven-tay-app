import sqlite3
import unittest

from database.seed import DEFAULT_DB_PATH, seed_database


class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        self.db_path = DEFAULT_DB_PATH
        seed_database(self.db_path)

    def test_database_exists(self):
        """Verify the database file exists."""
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

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        for table in expected_tables:
            self.assertIn(
                table,
                tables,
                f"Mandatory table '{table}' is missing "
                "from the database schema.",
            )

    def test_clinician_npi_constraint(self):
        """Verify that clinicians table contains the NPI column."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(clinicians);")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        self.assertIn(
            "npi_number",
            columns,
            "The 'npi_number' column is missing from the clinicians table.",
        )

    def test_clinician_npi_must_be_ten_digits(self):
        """Reject malformed clinician identifiers at the database boundary."""
        with sqlite3.connect(self.db_path) as connection, self.assertRaises(
            sqlite3.IntegrityError
        ):
            connection.execute(
                "INSERT INTO clinicians "
                "(id, full_name, npi_number, contact_phone) "
                "VALUES (?, ?, ?, ?)",
                ("invalid-npi", "Test Clinician", "123456789X", "555-0100"),
            )


if __name__ == '__main__':
    unittest.main()
