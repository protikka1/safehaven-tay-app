"""Safety regression checks for the non-clinical demonstration workflow."""
import unittest
from pathlib import Path

from database.age_routing import age_route
from database.seed import seed_database
from database.db import get_connection
from tempfile import TemporaryDirectory


class IntakeSafetyTests(unittest.TestCase):
    def test_age_routes(self):
        self.assertEqual(age_route(15), "minor_safeguarding")
        self.assertEqual(age_route(17), "minor_safeguarding")
        self.assertEqual(age_route(18), "tay")
        self.assertEqual(age_route(25), "adult_referral")
        self.assertEqual(age_route(None), "age_unknown")

    def test_no_automatic_placement_or_prescription_in_entrypoints(self):
        for path in ("app.py", "database/simulate_intake.py"):
            source = Path(path).read_text(encoding="utf-8").lower()
            self.assertNotIn("insert into mat_prescriptions", source, path)
            self.assertNotIn("insert into program_placements", source, path)

    def test_synthetic_fixture_does_not_auto_place(self):
        source = Path("tests/fixtures/seed_100_mock_youth.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("insert into program_placements", source)
        self.assertNotIn("insert into mat_prescriptions", source)

    def test_age_unknown_and_minor_request_saved_without_placement(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "safety.db"
            seed_database(db_path)
            with get_connection(db_path) as conn:
                for idx, age in enumerate((None, 14), start=1):
                    conn.execute(
                        "INSERT INTO low_barrier_intakes (intake_code, approximate_age, immediate_need, intake_method) VALUES (?, ?, 'shelter', 'web')",
                        (f"SAFETY-{idx}", age),
                    )
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM low_barrier_intakes").fetchone()[0], 2)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM program_placements").fetchone()[0], 0)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM mat_prescriptions").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
