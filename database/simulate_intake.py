import sqlite3
import json
import uuid
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).with_name("recovery_app.db")

# Sample quick intake payload mimicking our fouth artifact (recovery-app-api-payloads.md)
INTAKE_PAYLOAD = {
    "alias": "Sky",
    "first_name": "Tyler",  # optional legal details
    "last_name": "Skyid",
    "date_of_birth": "2004-10-12", # TAY (Transition-Age Youth aged ~21)
    "phone_number": "213-555-0999",
    "emergency_contact": "Aunt Jessie (323-555-0777)",
    "assessment": {
        "assessment_type": "SUD_Screening",
        "primary_substance": "Opioids/Fentanyl",
        "overdose_history_count": 2,
        "housing_status_at_intake": "Unsheltered",
        "notes": "Youth expressed willingness to stabilize and requested MAT options."
    },
    "booking": {
        "facility_type": "Substance_Use_Hub"  # Prefers Substance_Use_Hub with empty beds
    }
}

def process_intake(db_path, payload):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    try:
        print(f"--- STARTING LOW-BARRIER INTAKE FOR ALIAS: '{payload['alias']}' ---")
        
        # Step 1: Create Youth Profile
        youth_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO youth_profiles (id, alias, first_name, last_name, date_of_birth, phone_number, emergency_contact)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            youth_id, 
            payload['alias'], 
            payload.get('first_name'), 
            payload.get('last_name'), 
            payload['date_of_birth'], 
            payload.get('phone_number'), 
            payload.get('emergency_contact')
        ))
        print(f"[SUCCESS] Registered profile: ID={youth_id}, Alias='{payload['alias']}'")
        
        # Step 2: Fetch an active caseworker (e.g., Peer Support Specialist or Housing Navigator)
        cursor.execute("SELECT id, full_name, role FROM caseworkers WHERE role = 'Peer Support Specialist' LIMIT 1;")
        caseworker = cursor.fetchone()
        if not caseworker:
            raise ValueError("No available Peer Support Specialists in database.")
        cw_id, cw_name, cw_role = caseworker
        
        # Assign Caseworker
        cursor.execute("""
            INSERT INTO care_assignments (id, youth_id, caseworker_id, relationship_type)
            VALUES (?, ?, ?, 'Primary Peer Advocate');
        """, (str(uuid.uuid4()), youth_id, cw_id))
        print(f"[SUCCESS] Assigned care advocate: {cw_name} ({cw_role})")
        
        # Step 3: Run Intake Screening Assessment
        assessment_id = str(uuid.uuid4())
        assessment_data = payload['assessment']
        cursor.execute("""
            INSERT INTO assessments (id, youth_id, assessor_id, assessment_type, primary_substance, overdose_history_count, housing_status_at_intake, assessment_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            assessment_id,
            youth_id,
            cw_id,
            assessment_data['assessment_type'],
            assessment_data['primary_substance'],
            assessment_data['overdose_history_count'],
            assessment_data['housing_status_at_intake'],
            json.dumps({"clinical_notes": assessment_data['notes']})
        ))
        print(f"[SUCCESS] Saved intake assessment: ID={assessment_id}, Risk='HIGH' due to Overdose History Count={assessment_data['overdose_history_count']}")
        
        # No automatic placement or prescribing: a qualified provider must accept
        # any placement and an authorized clinician must approve treatment.
        print("[PENDING] Human review required for shelter placement and clinical care.")

        conn.commit()
        print("--- INTAKE RECORDED; PLACEMENT AND TREATMENT PENDING ---")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Transaction failed: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    process_intake(DB_PATH, INTAKE_PAYLOAD)
