"""Record low-barrier intake, check bed candidates, and assign coordinator review."""

from contextlib import closing
from pathlib import Path
import secrets

from database.age_routing import age_route
from database.db import get_connection


def record_request(db_path: Path, age: int | None, treatment_requested: bool):
    route = age_route(age)
    code = "SH-" + secrets.token_hex(12).upper()
    with closing(get_connection(db_path)) as conn, conn:
        conn.execute(
            """INSERT INTO low_barrier_intakes
               (intake_code, approximate_age, immediate_need, intake_method, status)
               VALUES (?, ?, ?, 'web', 'assessment')""",
            (code, age, "recovery" if treatment_requested else "shelter"),
        )
        beds = []
        if route == "tay":
            beds = conn.execute(
                """SELECT name, contact_phone FROM facilities
                   WHERE available_beds > 0
                     AND facility_type IN ('TAY_Shelter', 'Youth_Shelter', 'TAY_Transitional_Housing')
                   ORDER BY available_beds DESC, name""",
            ).fetchall()
    return code, route, beds


def assign_caseworker(db_path: Path, intake_id: int, caseworker_id: str) -> None:
    with closing(get_connection(db_path)) as conn, conn:
        result = conn.execute(
            """INSERT INTO intake_caseworker_assignments (intake_id, caseworker_id)
               SELECT i.id, c.id FROM low_barrier_intakes i JOIN caseworkers c
               ON c.id = ? AND c.is_active = 1
               WHERE i.id = ? AND i.status IN ('open', 'assessment', 'service_pending')
               ON CONFLICT(intake_id) DO NOTHING""",
            (caseworker_id, intake_id),
        )
        if result.rowcount != 1:
            raise ValueError("Refresh the queue and select an open intake and an active caseworker.")
        conn.execute(
            """UPDATE low_barrier_intakes SET status = 'case_manager_assigned',
               updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (intake_id,),
        )
