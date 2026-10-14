import sqlite3
import unittest

from database.age_routing import age_route


class AgeRoutingTests(unittest.TestCase):

    def test_minor_routes_to_safeguarding(self):
        self.assertEqual(age_route(14), "minor_safeguarding")
        self.assertEqual(age_route(17), "minor_safeguarding")

    def test_tay_boundary(self):
        self.assertEqual(age_route(18), "tay")
        self.assertEqual(age_route(24), "tay")

    def test_adult_routes_to_referral(self):
        self.assertEqual(age_route(25), "adult_referral")

    def test_unknown_age_is_accepted(self):
        self.assertEqual(age_route(None), "age_unknown")

    def test_invalid_age_is_rejected(self):
        with self.assertRaises(ValueError):
            age_route(-1)

        with self.assertRaises(ValueError):
            age_route(121)

    def test_boolean_is_not_an_age(self):
        with self.assertRaises(TypeError):
            age_route(True)
        with self.assertRaises(TypeError):
            age_route(False)

    def test_schema_accepts_minor_tay_adult_and_unknown(self):
        connection = sqlite3.connect(":memory:")

        with open("database/schema.sql", encoding="utf-8") as schema:
            connection.executescript(schema.read())

        for number, age in enumerate((14, 17, 18, 24, 25, None), start=1):
            connection.execute(
                """
                INSERT INTO low_barrier_intakes
                    (intake_code, approximate_age, immediate_need, intake_method)
                VALUES (?, ?, ?, ?)
                """,
                (
                    f"AGE-TEST-{number}",
                    age,
                    "shelter",
                    "self_checkin",
                ),
            )

        count = connection.execute(
            "SELECT COUNT(*) FROM low_barrier_intakes"
        ).fetchone()[0]

        self.assertEqual(count, 6)
        connection.close()


if __name__ == "__main__":
    unittest.main()
