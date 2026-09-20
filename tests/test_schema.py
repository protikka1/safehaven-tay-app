import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.seed import seed_database

EXPECTED_TABLES = {
    "low_barrier_intakes","youth_profiles","caseworkers","clinicians","facilities",
    "assessments","care_assignments","mat_prescriptions","program_placements",
    "recovery_milestones","digital_activity_traces",
}

class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.db"
        seed_database(self.db_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_core_tables_exist(self):
        with sqlite3.connect(self.db_path) as connection:
            tables={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue(EXPECTED_TABLES.issubset(tables), EXPECTED_TABLES - tables)

    def test_foreign_keys_and_integrity(self):
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0],1)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(),[])
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0],"ok")

    def test_clinician_npi_constraint(self):
        with sqlite3.connect(self.db_path) as connection:
            columns=[r[1] for r in connection.execute("PRAGMA table_info(clinicians)")]
        self.assertIn("npi_number",columns)

    def test_low_barrier_intake_accepts_miscellaneous(self):
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                "INSERT INTO low_barrier_intakes (intake_code,immediate_need,intake_method) VALUES (?,?,?)",
                ("SH-TAY-TEST","miscellaneous","web"),
            )
            self.assertEqual(connection.execute("SELECT immediate_need FROM low_barrier_intakes WHERE intake_code=?",("SH-TAY-TEST",)).fetchone()[0],"miscellaneous")

if __name__ == "__main__":
    unittest.main()
