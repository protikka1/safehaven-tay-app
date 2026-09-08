"""Run a synthetic intake simulation; all identities and contacts are fictional."""

import json
import sqlite3
import uuid
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "recovery_app.db"

# Sample quick intake payload for the local recovery workflow.
INTAKE_PAYLOAD = {
    "alias": "Example-Youth-001",
    "first_name": "ExampleFirst",  # optional legal details
    "last_name": "ExampleLast",
    "date_of_birth": "2004-10-12",  # TAY (Transition-Age Youth aged ~21)
    "safelink_phone_number": "213-555-0999",
    "emergency_contact": "Example Relative (213-555-0100)",
    "assessment": {
        "assessment_type": "SUD_Screening",
        "primary_substance": "Opioids/Fentanyl",
        "overdose_history_count": 2,
        "housing_status_at_intake": "Unsheltered",
        "notes": (
            "Youth expressed willingness to stabilize and requested MAT options."
        )
    },
    "booking": {
        "facility_type": "Substance_Use_Hub",
        # Prefers Substance_Use_Hub with empty beds.
    }
}

def process_intake(db_path, payload):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    try:
        print(
            "--- STARTING LOW-BARRIER INTAKE FOR ALIAS: "
            f"'{payload['alias']}' ---"
        )

        # Step 1: Create Youth Profile
        youth_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO youth_profiles (
                id,
                alias,
                first_name,
                last_name,
                date_of_birth,
                safelink_phone_number,
                emergency_contact
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            youth_id,
            payload['alias'],
            payload.get('first_name'),
            payload.get('last_name'),
            payload['date_of_birth'],
            payload.get('safelink_phone_number'),
            payload.get('emergency_contact')
        ))
        print(
            f"[SUCCESS] Registered profile: ID={youth_id}, "
            f"Alias='{payload['alias']}'"
        )

        # Step 2: Fetch an active caseworker
        # (e.g., Peer Support Specialist or Housing Navigator)
        cursor.execute(
            "SELECT id, full_name, role FROM caseworkers "
            "WHERE role = 'Peer Support Specialist' LIMIT 1;"
        )
        caseworker = cursor.fetchone()
        if not caseworker:
            raise ValueError(
                "No available Peer Support Specialists in database."
            )
        cw_id, cw_name, cw_role = caseworker

        # Assign Caseworker
        cursor.execute("""
            INSERT INTO care_assignments (
                id,
                youth_id,
                caseworker_id,
                relationship_type
            )
            VALUES (?, ?, ?, 'Primary Peer Advocate');
        """, (str(uuid.uuid4()), youth_id, cw_id))
        print(f"[SUCCESS] Assigned care advocate: {cw_name} ({cw_role})")

        # Step 3: Run Intake Screening Assessment
        assessment_id = str(uuid.uuid4())
        assessment_data = payload['assessment']
        cursor.execute(
            """
            INSERT INTO assessments (
                id,
                youth_id,
                assessor_id,
                assessment_type,
                primary_substance,
                overdose_history_count,
                housing_status_at_intake,
                assessment_payload
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                assessment_id,
                youth_id,
                cw_id,
                assessment_data['assessment_type'],
                assessment_data['primary_substance'],
                assessment_data['overdose_history_count'],
                assessment_data['housing_status_at_intake'],
                json.dumps({"clinical_notes": assessment_data['notes']})
            ),
        )
        print(
            f"[SUCCESS] Saved intake assessment: ID={assessment_id}, "
            "Risk='HIGH' due to Overdose History Count="
            f"{assessment_data['overdose_history_count']}"
        )

        # Step 4: Booking & Bed Reservation
        # (First available in Substance_Use_Hub or Detox_Center)
        cursor.execute("""
            SELECT id, name, available_beds
            FROM facilities
            WHERE facility_type = 'Substance_Use_Hub'
            AND available_beds > 0
            LIMIT 1;
        """)
        target_facility = cursor.fetchone()

        if not target_facility:
            # Fallback to Detox_Center
            cursor.execute("""
                SELECT id, name, available_beds
                FROM facilities
                WHERE facility_type = 'Detox_Center'
                AND available_beds > 0
                LIMIT 1;
            """)
            target_facility = cursor.fetchone()
            
        if not target_facility:
            raise ValueError(
                "All detox centers and substance use hubs are fully "
                "booked. No available empty beds."
            )

        fac_id, fac_name, fac_beds = target_facility
        print(
            f"[INFO] Facility chosen: '{fac_name}' "
            f"(Empty beds before booking: {fac_beds})"
        )

        # Decrement Available Beds
        new_beds = fac_beds - 1
        cursor.execute("""
            UPDATE facilities 
            SET available_beds = ? 
            WHERE id = ?;
        """, (new_beds, fac_id))
        
        # Log Placement
        placement_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO program_placements (
                id,
                youth_id,
                facility_id,
                placement_type,
                start_date,
                status
            )
            VALUES (?, ?, ?, 'Detox_Stay', ?, 'Enrolled');
        """, (placement_id, youth_id, fac_id, date.today().isoformat()))
        print(
            "[SUCCESS] Lock & Booked: "
            f"Placement ID={placement_id} at '{fac_name}'. "
            f"Available beds remaining: {new_beds}"
        )

        # Step 5: Initialize MAT Treatment Script linking to a local
        # Clinician
        cursor.execute(
            "SELECT id, full_name, npi_number FROM clinicians LIMIT 1;"
        )
        clinician = cursor.fetchone()
        if not clinician:
            raise ValueError("No available clinicians found to issue MAT script.")
        clin_id, clin_name, clin_npi = clinician
        
        prescription_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO mat_prescriptions (
                id,
                youth_id,
                prescribing_clinician_id,
                medication_name,
                dosage_instructions,
                start_date,
                end_date,
                dispensing_facility_id
            )
            VALUES (
                ?, ?, ?, 'Buprenorphine',
                '8mg sublingual strip daily under peer observation',
                ?, ?, ?
            );
            """,
            (
                prescription_id,
                youth_id,
                clin_id,
                date.today().isoformat(),
                (date.today() + timedelta(days=30)).isoformat(),
                fac_id
            ),
        )
        print(
            "[SUCCESS] Issued MAT prescription script: "
            f"ID={prescription_id} for 'Buprenorphine' signed by "
            f"{clin_name} (NPI: {clin_npi})"
        )

        conn.commit()
        print("--- INTAKE AND BOOKING COMPLETED FLawlessly WITHOUT BARRIERS ---")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Transaction failed: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    process_intake(DB_PATH, INTAKE_PAYLOAD)
