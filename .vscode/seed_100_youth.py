import sqlite3
import random
import uuid
from datetime import datetime, timedelta

# Database path (creating a newly populated test database in scratch first)
DB_PATH = "/workspace/scratch/recovery_app_populated.db"

def setup_and_seed_100_youth():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Enable Foreign Key Constraints
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Re-create tables to guarantee clean schema
    cursor.execute("""
    DROP TABLE IF EXISTS digital_activity_traces;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS recovery_milestones;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS program_placements;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS mat_prescriptions;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS care_assignments;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS assessments;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS facilities;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS clinicians;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS caseworkers;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS youth_profiles;
    """)

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
    );""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caseworkers (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        assigned_agency TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinicians (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        npi_number TEXT UNIQUE NOT NULL,
        specialty TEXT DEFAULT 'Addiction Medicine',
        contact_phone TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );""")
    
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
    );""")
    
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
    );""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS care_assignments (
        id TEXT PRIMARY KEY,
        youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
        caseworker_id TEXT REFERENCES caseworkers(id) ON DELETE CASCADE,
        relationship_type TEXT DEFAULT 'Primary Case Manager',
        assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Active',
        UNIQUE(youth_id, caseworker_id, relationship_type)
    );""")
    
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
    );""")
    
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
    );""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recovery_milestones (
        id TEXT PRIMARY KEY,
        youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
        milestone_type TEXT NOT NULL,
        description TEXT NOT NULL,
        achieved_at TEXT DEFAULT CURRENT_TIMESTAMP,
        verified_by_staff_id TEXT REFERENCES caseworkers(id),
        verification_notes TEXT
    );""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS digital_activity_traces (
        id TEXT PRIMARY KEY,
        youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
        action_type TEXT NOT NULL,
        app_version TEXT,
        device_os TEXT,
        action_payload TEXT, 
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );""")
    
    conn.commit()

    # Seed core actors (facilities, caseworkers, clinicians)
    fac_ids = [str(uuid.uuid4()) for _ in range(3)]
    facilities_data = [
        (fac_ids[0], "Skid Row Substance Use Health Hub", "Substance_Use_Hub", "600 San Pedro St, Los Angeles, CA 90013", "213-555-0199", 40, 8),
        (fac_ids[1], "Hilda L. Solis Care First Village", "Detox_Center", "1060 Vignes St, Los Angeles, CA 90012", "213-555-0102", 50, 15),
        (fac_ids[2], "Weingart Tower PSH", "PSH_Complex", "566 S San Pedro St, Los Angeles, CA 90013", "213-627-9000", 120, 2)
    ]
    cursor.executemany("INSERT OR REPLACE INTO facilities (id, name, facility_type, street_address, contact_phone, total_capacity, available_beds) VALUES (?, ?, ?, ?, ?, ?, ?);", facilities_data)

    cw_ids = [str(uuid.uuid4()) for _ in range(4)]
    caseworkers_data = [
        (cw_ids[0], "Marcus Henderson", "Peer Support Specialist", "VOA TAY Drop-In Center", "213-555-0111", 1),
        (cw_ids[1], "Elena Rostova", "Housing Navigator", "Weingart Tower PSH",
         "213-555-0222", 1),
        (cw_ids[2], "Sarah Jenkins", "Social Worker", "Midnight Mission",
         "213-555-0333", 1),
        (cw_ids[3], "Darnell West", "Peer Support Specialist", "Skid Row Substance Use Health Hub", "213-555-0444", 1)
    ]
    cursor.executemany("INSERT OR REPLACE INTO caseworkers (id, full_name, role, assigned_agency, contact_phone, is_active) VALUES (?, ?, ?, ?, ?, ?);", caseworkers_data)

    clin_ids = [str(uuid.uuid4()) for _ in range(2)]
    clinicians_data = [
        (clin_ids[0], "Dr. Karen Gill, M.D.", "1881678364", "Addiction Medicine", "213-555-0800"),
        (clin_ids[1], "Dr. Morton J. Cowan, M.D.", "1905766355", "Pediatric Immunology", "415-555-1278")
    ]
    cursor.executemany("INSERT OR REPLACE INTO clinicians (id, full_name, npi_number, specialty, contact_phone) VALUES (?, ?, ?, ?, ?);", clinicians_data)
    conn.commit()

    # Generate 100 high-fidelity TAY mock profiles
    first_names = ["Jordan", "Taylor", "Alex", "Jayden", "Angel", "Sky", "River", "Sam", "Morgan", "Casey", 
                   "Jamie", "Skyler", "Charlie", "Hayden", "Robin", "Dakota", "Phoenix", "Dallas", "Devon", "Jesse",
                   "Justice", "Amari", "Reese", "Rowan", "Emery", "Avery", "Blake", "Logan", "Parker", "Riley"]
    last_names = ["Smith", "Jones", "Brown", "Johnson", "Davis", "Miller", "Wilson", "Taylor", "Thomas", "Jackson", 
                  "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis"]
    aliases_pool = ["Sky", "Phoenix", "River", "Shadow", "Ace", "Chance", "Glimmer", "Ghost", "Starlight", "Hope", 
                    "Slick", "Solo", "Doc", "Blade", "Red", "Blue", "Tiny", "Smiley", "Chief", "Breeze", "Echo", "Nova"]
    substances = ["Opioids", "Stimulants", "Alcohol", "Benzodiazepines", "Multiple", "Cannabis", "None"]
    housing_statuses = ["Unsheltered", "SRO", "Transitional", "Emergency Shelter"]

    # Current year is 2026. TAY are ages 18 to 24 (Born 2002 to 2008)
    for i in range(1, 101):
        youth_id = str(uuid.uuid4())
        alias = f"{random.choice(aliases_pool)}-{i}"
        fname = random.choice(first_names) if random.random() > 0.15 else None
        lname = random.choice(last_names) if fname and random.random() > 0.2 else None
        
        # Calculate birthdate for age 18-24 in 2026
        birth_year = random.randint(2002, 2008)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        dob = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
        
        phone = f"213-555-{random.randint(1000, 9999)}" if random.random() > 0.3 else None
        emergency = f"Contact relative: {random.randint(213, 818)}-555-{random.randint(1000, 9999)}" if random.random() > 0.5 else "None"
        
        # Insert Youth Profile
        cursor.execute("""
            INSERT INTO youth_profiles (id, alias, first_name, last_name, date_of_birth, safelink_phone_number, emergency_contact)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (youth_id, alias, fname, lname, dob, phone, emergency))
        
        # 1. Assessments
        ass_id = str(uuid.uuid4())
        ass_type = random.choice(["SUD_Screening", "Housing_Needs", "CalWORKs_Appraisal"])
        prim_sub = random.choice(substances)
        od_count = random.randint(0, 4) if prim_sub in ["Opioids", "Stimulants", "Multiple"] else 0
        h_status = random.choice(housing_statuses)
        payload = f'{{"vulnerability_index": {random.randint(1, 10)}, "notes": "Low-barrier intake screening complete"}}'
        
        cursor.execute("""
            INSERT INTO assessments (id, youth_id, assessor_id, assessment_type, primary_substance, overdose_history_count, housing_status_at_intake, assessment_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (ass_id, youth_id, random.choice(cw_ids), ass_type, prim_sub, od_count, h_status, payload))

        # 2. Care Assignments
        care_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO care_assignments (id, youth_id, caseworker_id, relationship_type, status)
            VALUES (?, ?, ?, ?, 'Active');
        """, (care_id, youth_id, random.choice(cw_ids), random.choice(["Primary Case Manager", "Peer Support", "Housing Navigator"])))

        # 3. MAT Prescriptions (Seed for those with opioid history/high vulnerability)
        if prim_sub in ["Opioids", "Multiple"] and random.random() > 0.2:
            mat_id = str(uuid.uuid4())
            med_name = random.choice(["Buprenorphine", "Methadone", "Naltrexone"])
            dosage = "16mg daily sublingual film" if med_name == "Buprenorphine" else "Daily clinical dose"
            start_dt = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
            end_dt = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                INSERT INTO mat_prescriptions (id, youth_id, prescribing_clinician_id, medication_name, dosage_instructions, start_date, end_date, adherence_status, dispensing_facility_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', ?);
            """, (mat_id, youth_id, random.choice(clin_ids), med_name, dosage, start_dt, end_dt, random.choice(fac_ids)))

        # 4. Program Placements
        if random.random() > 0.4:
            placement_id = str(uuid.uuid4())
            p_type = random.choice(["Detox_Stay", "Inpatient_Rehab", "Supportive_Housing"])
            start_dt = (datetime.now() - timedelta(days=random.randint(1, 45))).strftime("%Y-%m-%d")
            
            cursor.execute("""
                INSERT INTO program_placements (id, youth_id, facility_id, placement_type, start_date, status)
                VALUES (?, ?, ?, ?, ?, 'Enrolled');
            """, (placement_id, youth_id, random.choice(fac_ids), p_type, start_dt))

        # 5. Recovery Milestones
        if random.random() > 0.3:
            milestone_id = str(uuid.uuid4())
            m_type = random.choice(["7_Day_MAT_Adherence", "Counseling_Completed", "Housing_Placement"])
            m_desc = f"Verified completion of {m_type.replace('_', ' ')}."
            
            cursor.execute("""
                INSERT INTO recovery_milestones (id, youth_id, milestone_type, description, verified_by_staff_id, verification_notes)
                VALUES (?, ?, ?, ?, ?, 'System auto-verified & caseworker signed off');
            """, (milestone_id, youth_id, m_type, m_desc, random.choice(cw_ids)))

        # 6. Digital Activity Traces (Simulate active app interaction history)
        for _ in range(random.randint(1, 3)):
            trace_id = str(uuid.uuid4())
            act_type = random.choice(["Prescription_Refill_Request", "Chatbot_SUD_Inquiry", "GPS_Safe_Zone_CheckIn"])
            cursor.execute("""
                INSERT INTO digital_activity_traces (id, youth_id, action_type, app_version, device_os, action_payload)
                VALUES (?, ?, ?, '1.2.0', ?, '{"interaction_duration_seconds": 45}');
            """, (trace_id, youth_id, act_type, random.choice(["Android", "iOS"])))

    conn.commit()
    conn.close()
    print("Database seeded with exactly 100 high-fidelity Transition-Age Youth (TAY) profiles across 10 tables.")

if __name__ == "__main__":
    setup_and_seed_100_youth()