"""Create a local SafeHaven database using synthetic reference data only."""
from __future__ import annotations
import argparse
from pathlib import Path
from database.db import DEFAULT_DB_PATH, get_connection

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "database" / "schema.sql"

def seed_reference_data(connection):
    connection.executemany(
        "INSERT OR IGNORE INTO facilities (id,name,facility_type,street_address,contact_phone,total_capacity,available_beds) VALUES (?,?,?,?,?,?,?)",
        [
            ("facility-health-hub","Example Recovery Health Hub","Substance_Use_Hub","100 Example Avenue, Test City, CA 90000","213-555-0199",40,8),
            ("facility-detox-village","Example Care First Village","Detox_Center","200 Example Avenue, Test City, CA 90000","213-555-0102",50,15),
        ],
    )
    connection.execute(
        "INSERT OR IGNORE INTO caseworkers (id,full_name,role,assigned_agency,contact_phone,is_active) VALUES (?,?,?,?,?,?)",
        ("caseworker-example","Example Caseworker One","Peer Support Specialist","Example TAY Service Agency","213-555-0111",1),
    )
    connection.execute(
        "INSERT OR IGNORE INTO clinicians (id,full_name,npi_number,specialty,contact_phone) VALUES (?,?,?,?,?)",
        ("clinician-example","Dr. Example Clinician","0000000000","Addiction Medicine","213-555-0800"),
    )

def seed_database(db_path: Path = DEFAULT_DB_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        seed_reference_data(connection)
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations: {violations}")
    return db_path

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db",type=Path,default=DEFAULT_DB_PATH)
    args=parser.parse_args()
    print(f"Initialized {seed_database(args.db)}")
