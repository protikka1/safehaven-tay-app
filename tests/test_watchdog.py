import unittest

from fccw_watchdog import audit_project, replacement_ledger_status


class TestWatchdog(unittest.TestCase):
    def test_inside_boundary_below_threshold_is_critical(self):
        result = audit_project(34.042, -118.248, 15)
        self.assertEqual(result.status, "CRITICAL VIOLATION")

    def test_inside_boundary_at_threshold_passes(self):
        result = audit_project(34.042, -118.248, 80)
        self.assertEqual(result.status, "PASS")

    def test_sro_replacement_is_one_for_one(self):
        self.assertEqual(replacement_ledger_status(12, 12).status, "PASS")
        self.assertEqual(
            replacement_ledger_status(12, 11).status,
            "CRITICAL VIOLATION",
        )


if __name__ == "__main__":
    unittest.main()
