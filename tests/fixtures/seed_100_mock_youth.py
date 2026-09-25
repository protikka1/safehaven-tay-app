"""Generate 100 deterministic synthetic TAY records for SafeHaven tests.

This fixture uses database.seed.seed_database() so database/schema.sql remains
the single source of truth. It never creates MAT prescriptions automatically.
"""

from __future__ import annotations

import json
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

from database.db import get_connection
from database.seed import seed_database

TEST_DB_PATH = Path(__file__).with_name("recovery_app_mock_100.db")
RANDOM_SEED = 42


def _uid(prefix: str, number: int) -> str:
    return f"{prefix}-{number:03d}-{uuid.uuid5(uuid.NAMESPACE_URL, f'safehaven-mock-{prefix}-{number}')}"


def seed_100_mock_youth(db_path: Path = TEST_DB_PATH) -> Path:
    """Create a fresh synthetic test DB and insert exactly 100 mock youth."""
    random.seed(RANDOM_SEED)
    db_path = Path(db_path)

    # This file is test-only. Remove a previous mock DB so each run starts clean.
    if db_path.exists():
        db_path.unlink()

    seed_database(db_path)

    first_names = [
        "Jordan", "Taylor", "Alex", "Jayden", "Angel", "Sky", "River", "Sam",
        "Morgan", "Casey", "Jamie", "Skyler", "Charlie", "Hayden", "Robin",
        "Dakota", "Phoenix", "Dallas", "Devon", "Jesse", "Justice", "Amari",
        "Reese", "Rowan", "Emery", "Avery", "Blake", "Logan", "Parker", "Riley",
    ]
    last_names = [
        "Smith", "Jones", "Brown", "Johnson", "Davis", "Miller", "Wilson",
        "Taylor", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson",
        "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis",
    ]
    aliases = [
        "Sky", "Phoenix", "River", "Shadow", "Ace", "Chance", "Glimmer",
        "Ghost", "Starlight", "Hope", "Slick", "Solo", "Doc", "Blade", "Red",
        "Blue", "Tiny", "Smiley", "Chief", "Breeze", "Echo", "Nova",
    ]
    substances = [
        "Opioids", "Stimulants", "Alcohol", "Benzodiazepines",
        "Multiple", "Cannabis", "None",
    ]
    housing_statuses = [
        "Unsheltered", "SRO", "Transitional", "Emergency Shelter",
    ]
    immediate_needs = ["shelter", "detox", "medical", "recovery", "miscellaneous"]
    intake_methods = ["self_checkin", "caseworker", "kiosk", "web"]
    urgency_levels = ["standard", "urgent", "emergency"]
    carriers = ["Example Mobile", "Test Wireless", "Demo Cellular", None]
    contact_methods = ["phone", "text", "caseworker", "in_person"]

    today = date.today()

    with get_connection(db_path) as connection:
        caseworker_ids = [
            row["id"]
            for row in connection.execute(
                "SELECT id FROM caseworkers WHERE is_active = 1 ORDER BY id"
            )
        ]
        facility_ids = [
            row["id"]
            for row in connection.execute("SELECT id FROM facilities ORDER BY id")
        ]

        if not caseworker_ids:
            raise RuntimeError("Reference seed produced no active caseworkers.")
        if not facility_ids:
            raise RuntimeError("Reference seed produced no facilities.")

        for i in range(1, 101):
            alias = f"{random.choice(aliases)}-{i}"
            approximate_age = random.randint(18, 24)
            intake_code = f"MOCK-{i:03d}"

            intake_cursor = connection.execute(
                """
                INSERT INTO low_barrier_intakes (
                    intake_code, street_alias, approximate_age, immediate_need,
                    intake_method, urgency_level, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    intake_code,
                    alias,
                    approximate_age,
                    random.choice(immediate_needs),
                    random.choice(intake_methods),
                    random.choice(urgency_levels),
                    "assessment",
                ),
            )
            intake_id = intake_cursor.lastrowid

            youth_id = _uid("youth", i)
            first_name = random.choice(first_names) if random.random() > 0.15 else None
            last_name = (
                random.choice(last_names)
                if first_name is not None and random.random() > 0.20
                else None
            )

            birth_year = today.year - approximate_age
            dob = f"{birth_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"

            phone_available = 1 if random.random() > 0.30 else 0
            phone_number = (
                f"213-555-{1000 + i:04d}" if phone_available else None
            )
            mobile_carrier = random.choice(carriers) if phone_available else None
            preferred_contact_method = (
                random.choice(["phone", "text"]) if phone_available
                else random.choice(["caseworker", "in_person"])
            )

            connection.execute(
                """
                INSERT INTO youth_profiles (
                    id, intake_id, alias, first_name, last_name, date_of_birth,
                    phone_number, mobile_carrier, phone_available,
                    preferred_contact_method, emergency_contact
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    youth_id,
                    intake_id,
                    alias,
                    first_name,
                    last_name,
                    dob,
                    phone_number,
                    mobile_carrier,
                    phone_available,
                    preferred_contact_method,
                    None,
                ),
            )

            caseworker_id = random.choice(caseworker_ids)
            primary_substance = random.choice(substances)
            overdose_count = (
                random.randint(0, 4)
                if primary_substance in {"Opioids", "Stimulants", "Multiple"}
                else 0
            )
            housing_status = random.choice(housing_statuses)

            assessment_payload = {
                "vulnerability_index": random.randint(1, 10),
                "notes": "Synthetic low-barrier intake screening.",
            }
            if primary_substance in {"Opioids", "Multiple"}:
                assessment_payload["clinical_review"] = (
                    "pending clinician authorization"
                )

            connection.execute(
                """
                INSERT INTO assessments (
                    id, youth_id, assessor_id, assessment_type,
                    primary_substance, overdose_history_count,
                    housing_status_at_intake, assessment_payload
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _uid("assessment", i),
                    youth_id,
                    caseworker_id,
                    random.choice(
                        ["SUD_Screening", "Housing_Needs", "General_Intake"]
                    ),
                    primary_substance,
                    overdose_count,
                    housing_status,
                    json.dumps(assessment_payload),
                ),
            )

            connection.execute(
                """
                INSERT INTO care_assignments (
                    id, youth_id, caseworker_id, relationship_type, status
                )
                VALUES (?, ?, ?, ?, 'Active')
                """,
                (
                    _uid("care", i),
                    youth_id,
                    caseworker_id,
                    random.choice(
                        ["Primary Case Manager", "Peer Support", "Housing Navigator"]
                    ),
                ),
            )

            if random.random() > 0.40:
                start_date = today - timedelta(days=random.randint(1, 45))
                connection.execute(
                    """
                    INSERT INTO program_placements (
                        id, youth_id, facility_id, placement_type, start_date, status
                    )
                    VALUES (?, ?, ?, ?, ?, 'Enrolled')
                    """,
                    (
                        _uid("placement", i),
                        youth_id,
                        random.choice(facility_ids),
                        random.choice(
                            ["Detox_Stay", "Inpatient_Rehab", "Supportive_Housing"]
                        ),
                        start_date.isoformat(),
                    ),
                )

            if random.random() > 0.30:
                milestone_type = random.choice(
                    ["Counseling_Completed", "Housing_Placement", "Service_Engagement"]
                )
                connection.execute(
                    """
                    INSERT INTO recovery_milestones (
                        id, youth_id, milestone_type, description,
                        verified_by_staff_id, verification_notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _uid("milestone", i),
                        youth_id,
                        milestone_type,
                        f"Synthetic test milestone: {milestone_type.replace('_', ' ')}.",
                        caseworker_id,
                        "Synthetic fixture; caseworker verification simulated for testing.",
                    ),
                )

            for trace_number in range(1, random.randint(1, 3) + 1):
                connection.execute(
                    """
                    INSERT INTO digital_activity_traces (
                        id, youth_id, action_type, app_version,
                        device_os, action_payload
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _uid(f"trace-{i}", trace_number),
                        youth_id,
                        random.choice(
                            [
                                "Service_Status_Check",
                                "Appointment_Request",
                                "Resource_Search",
                            ]
                        ),
                        "test-fixture",
                        random.choice(["Android", "iOS"]),
                        json.dumps({"synthetic": True}),
                    ),
                )

        profile_count = connection.execute(
            "SELECT COUNT(*) FROM youth_profiles"
        ).fetchone()[0]
        prescription_count = connection.execute(
            "SELECT COUNT(*) FROM mat_prescriptions"
        ).fetchone()[0]
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()

        if profile_count != 100:
            raise RuntimeError(f"Expected 100 mock profiles, found {profile_count}.")
        if prescription_count != 0:
            raise RuntimeError(
                f"Expected zero automatically generated prescriptions, found {prescription_count}."
            )
        if violations:
            raise RuntimeError(f"Foreign-key violations: {violations}")

    print(f"Created {db_path} with exactly 100 synthetic TAY mock profiles.")
    print("Automatic prescriptions created: 0")
    return db_path


if __name__ == "__main__":
    seed_100_mock_youth()
