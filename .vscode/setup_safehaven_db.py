import os
import sqlite3
import uuid

# Define the local database path within the project structure
DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "recovery-app.db")

def build_and_seed_db():
    # Ensure the directory exists
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print(f"Created directory: '{DB_DIR}'")

    print(f"Connecting to database at: '{DB_PATH}'")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable Foreign Key support in SQLite3
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Create youth_profiles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS youth_profiles (
        id TEXT PRIMARY KEY,
        alias TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        date_of_birth TEXT NOT NULL,
        safelink_phone_number TEXT,
        emergency_contact TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Create caseworkers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caseworkers (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        assigned_agency TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Create clinicians table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinicians (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        npi_number TEXT UNIQUE NOT NULL,
        specialty TEXT DEFAULT 'Addiction Medicine',
        contact_phone TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Create facilities table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facilities (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        facility_type TEXT NOT NULL,
        street_address TEXT NOT NULL,
        contact_phone TEXT,
        total_capacity INTEGER,
        available_beds INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Create assessments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        id TEXT PRIMARY KEY,
        youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
        assessor_id TEXT REFERENCES caseworkers(id),
        assessment_type TEXT NOT NULL,
        primary_substance TEXT,
        overdose_history_count INTEGER DEFAULT 0,
        housing_status_at_intake TEXT NOT NULL,
        assessment_payload TEXT,
        completed_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. Create care_assignments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS care_assignments (
        id TEXT PRIMARY KEY,
        youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
        caseworker_id TEXT REFERENCES caseworkers(id) ON DELETE CASCADE,
        relationship_type TEXT DEFAULT 'Primary Case Manager',
        assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Active',
        UNIQUE(youth_id, caseworker_id, relationship_type)
    );
    """)

    # 7. Create mat_prescriptions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mat_prescriptions (
        id TEXT PRIMARY KEY,
        youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
        prescribing_clinician_id TEXT REFERENCES clinicians(id),
        medication_name TEXT NOT NULL,
        dosage_instructions TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        adherence_status TEXT DEFAULT 'Active',
        dispensing_facility_id TEXT REFERENCES facilities(id),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8. Create program_placements table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS program_placements (
        id TEXT PRIMARY KEY,
        youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
        facility_id TEXT REFERENCES facilities(id),
        placement_type TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        discharge_reason TEXT,
        status TEXT DEFAULT 'Enrolled',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 9. Create recovery_milestones table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recovery_milestones (
        id TEXT PRIMARY KEY,
        youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
        milestone_type TEXT NOT NULL,
        description TEXT NOT NULL,
        achieved_at TEXT DEFAULT CURRENT_TIMESTAMP,
        verified_by_staff_id TEXT REFERENCES caseworkers(id),
        verification_notes TEXT
    );
    """)

    # 10. Create digital_activity_traces table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS digital_activity_traces (
        id TEXT PRIMARY KEY,
        youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
        action_type TEXT NOT NULL,
        app_version TEXT,
        device_os TEXT,
        action_payload TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    print("Success: Generated all 10 relational tables.")

    # --- SEEDING BASIC DATA ---
    print("Seeding initial high-fidelity data...")

    # Seed local support facilities
    facilities_data = [
        (str(uuid.uuid4()), "Skid Row Substance Use Health Hub", "Substance_Use_Hub", "600 San Pedro St, Los Angeles, CA 90013", "213-555-0199", 40, 8),
        (str(uuid.uuid4()), "Hilda L. Solis Care First Village", "Detox_Center", "1060 Vignes St, Los Angeles, CA 90012", "213-555-0102", 50, 15),
        (str(uuid.uuid4()), "Weingart Tower PSH", "PSH_Complex", "566 S San Pedro St, Los Angeles, CA 90013", "213-627-9000", 120, 2)
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO facilities (id, name, facility_type, street_address, contact_phone, total_capacity, available_beds)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, facilities_data)

    # Seed peer caseworkers and navigators
    caseworkers_data = [
        (str(uuid.uuid4()), "Marcus Henderson", "Peer Support Specialist", "VOA TAY Drop-In Center", "213-555-0111", 1),
        (str(uuid.uuid4()), "Elena Rostova", "Housing Navigator", "Weingart Tower PSH", "213-555-0222", 1),
        (str(uuid.uuid4()), "Darnell West", "Peer Support Specialist", "Skid Row Substance Use Health Hub", "213-555-0444", 1)
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO caseworkers (id, full_name, role, assigned_agency, contact_phone, is_active)
        VALUES (?, ?, ?, ?, ?, ?);
    """, caseworkers_data)

    # Seed authorized local physicians
    clinicians_data = [
        (str(uuid.uuid4()), "Dr. Karen Gill, M.D.", "1881678364", "Addiction Medicine", "213-555-0800"),
        (str(uuid.uuid4()), "Dr. Morton J. Cowan, M.D.", "1905766355", "Pediatric Immunology", "415-555-1278")
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO clinicians (id, full_name, npi_number, specialty, contact_phone)
        VALUES (?, ?, ?, ?, ?);
    """, clinicians_data)

    conn.commit()
    conn.close()
    print("Success: SQLite3 database fully initialized and seeded at database/recovery-app.db")

if __name__ == "__main__":
    build_and_seed_db()
