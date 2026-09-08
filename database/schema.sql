PRAGMA foreign_keys = ON;

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

CREATE TABLE IF NOT EXISTS caseworkers (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    assigned_agency TEXT NOT NULL,
    contact_phone TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clinicians (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    npi_number TEXT UNIQUE NOT NULL CHECK (
        length(npi_number) = 10 AND npi_number NOT GLOB '*[^0-9]*'
    ),
    specialty TEXT DEFAULT 'Addiction Medicine',
    contact_phone TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facilities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    facility_type TEXT NOT NULL,
    street_address TEXT NOT NULL,
    contact_phone TEXT,
    total_capacity INTEGER,
    available_beds INTEGER DEFAULT 0 CHECK (available_beds >= 0),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    assessor_id TEXT REFERENCES caseworkers(id),
    assessment_type TEXT NOT NULL,
    primary_substance TEXT,
    overdose_history_count INTEGER DEFAULT 0,
    housing_status_at_intake TEXT NOT NULL,
    assessment_payload TEXT,
    completed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS care_assignments (
    id TEXT PRIMARY KEY,
    youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    caseworker_id TEXT NOT NULL REFERENCES caseworkers(id) ON DELETE CASCADE,
    relationship_type TEXT DEFAULT 'Primary Case Manager',
    assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Active',
    UNIQUE(youth_id, caseworker_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS mat_prescriptions (
    id TEXT PRIMARY KEY,
    youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    prescribing_clinician_id TEXT NOT NULL REFERENCES clinicians(id),
    medication_name TEXT NOT NULL,
    dosage_instructions TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    adherence_status TEXT DEFAULT 'Active',
    dispensing_facility_id TEXT REFERENCES facilities(id),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS program_placements (
    id TEXT PRIMARY KEY,
    youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    facility_id TEXT REFERENCES facilities(id),
    placement_type TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    discharge_reason TEXT,
    status TEXT DEFAULT 'Enrolled',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recovery_milestones (
    id TEXT PRIMARY KEY,
    youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    milestone_type TEXT NOT NULL,
    description TEXT NOT NULL,
    achieved_at TEXT DEFAULT CURRENT_TIMESTAMP,
    verified_by_staff_id TEXT REFERENCES caseworkers(id),
    verification_notes TEXT
);

CREATE TABLE IF NOT EXISTS digital_activity_traces (
    id TEXT PRIMARY KEY,
    youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    app_version TEXT,
    device_os TEXT,
    action_payload TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
