PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS low_barrier_intakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_code TEXT NOT NULL UNIQUE,
    street_alias TEXT,
    approximate_age INTEGER CHECK (approximate_age IS NULL OR approximate_age BETWEEN 18 AND 24),
    immediate_need TEXT NOT NULL CHECK (immediate_need IN ('shelter','detox','medical','recovery','miscellaneous')),
    intake_method TEXT NOT NULL CHECK (intake_method IN ('self_checkin','caseworker','kiosk','web')),
    urgency_level TEXT NOT NULL DEFAULT 'standard' CHECK (urgency_level IN ('standard','urgent','emergency')),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','assessment','service_pending','placed','case_manager_assigned','reengaged','closed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS youth_profiles (
    id TEXT PRIMARY KEY,
    intake_id INTEGER UNIQUE REFERENCES low_barrier_intakes(id) ON DELETE SET NULL,
    alias TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    date_of_birth TEXT,
    phone_number TEXT,
    mobile_carrier TEXT,
    phone_available INTEGER NOT NULL DEFAULT 0 CHECK (phone_available IN (0,1)),
    preferred_contact_method TEXT,
    emergency_contact TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS caseworkers (
    id TEXT PRIMARY KEY, full_name TEXT NOT NULL, role TEXT NOT NULL,
    assigned_agency TEXT NOT NULL, contact_phone TEXT NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clinicians (
    id TEXT PRIMARY KEY, full_name TEXT NOT NULL,
    npi_number TEXT UNIQUE NOT NULL CHECK (length(npi_number)=10 AND npi_number NOT GLOB '*[^0-9]*'),
    specialty TEXT DEFAULT 'Addiction Medicine', contact_phone TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facilities (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, facility_type TEXT NOT NULL,
    street_address TEXT NOT NULL, contact_phone TEXT,
    total_capacity INTEGER CHECK (total_capacity IS NULL OR total_capacity >= 0),
    available_beds INTEGER DEFAULT 0 CHECK (available_beds >= 0),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    CHECK (total_capacity IS NULL OR available_beds <= total_capacity)
);

CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY, youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    assessor_id TEXT REFERENCES caseworkers(id), assessment_type TEXT NOT NULL,
    primary_substance TEXT, overdose_history_count INTEGER DEFAULT 0 CHECK (overdose_history_count >= 0),
    housing_status_at_intake TEXT, assessment_payload TEXT,
    completed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS care_assignments (
    id TEXT PRIMARY KEY, youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    caseworker_id TEXT NOT NULL REFERENCES caseworkers(id) ON DELETE CASCADE,
    relationship_type TEXT DEFAULT 'Primary Case Manager', assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Active', UNIQUE(youth_id,caseworker_id,relationship_type)
);

CREATE TABLE IF NOT EXISTS mat_prescriptions (
    id TEXT PRIMARY KEY, youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    prescribing_clinician_id TEXT NOT NULL REFERENCES clinicians(id),
    medication_name TEXT NOT NULL, dosage_instructions TEXT NOT NULL,
    start_date TEXT NOT NULL, end_date TEXT, adherence_status TEXT DEFAULT 'Active',
    dispensing_facility_id TEXT REFERENCES facilities(id),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS program_placements (
    id TEXT PRIMARY KEY, youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    facility_id TEXT REFERENCES facilities(id), placement_type TEXT NOT NULL,
    start_date TEXT NOT NULL, end_date TEXT, discharge_reason TEXT,
    status TEXT DEFAULT 'Enrolled', created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recovery_milestones (
    id TEXT PRIMARY KEY, youth_id TEXT NOT NULL REFERENCES youth_profiles(id) ON DELETE CASCADE,
    milestone_type TEXT NOT NULL, description TEXT NOT NULL,
    achieved_at TEXT DEFAULT CURRENT_TIMESTAMP,
    verified_by_staff_id TEXT REFERENCES caseworkers(id), verification_notes TEXT
);

CREATE TABLE IF NOT EXISTS digital_activity_traces (
    id TEXT PRIMARY KEY, youth_id TEXT REFERENCES youth_profiles(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL, app_version TEXT, device_os TEXT, action_payload TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_assessments_youth ON assessments(youth_id);
CREATE INDEX IF NOT EXISTS idx_care_assignments_youth ON care_assignments(youth_id);
CREATE INDEX IF NOT EXISTS idx_program_placements_youth ON program_placements(youth_id);
CREATE INDEX IF NOT EXISTS idx_recovery_milestones_youth ON recovery_milestones(youth_id);
