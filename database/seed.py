"""Create the local SafeHaven SQLite database from schema.sql."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "database" / "recovery_app.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def seed_reference_data(connection: sqlite3.Connection) -> None:
    """Add the minimum facilities and care team needed by local workflows."""
    connection.executemany(
        "INSERT OR IGNORE INTO facilities "
        "(id, name, facility_type, street_address, contact_phone, "
        "total_capacity, available_beds) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                "facility-health-hub",
                "Skid Row Substance Use Health Hub",
                "Substance_Use_Hub",
                "600 San Pedro St, Los Angeles, CA 90013",
                "213-555-0199",
                40,
                8,
            ),
            (
                "facility-detox-village",
                "Hilda L. Solis Care First Village",
                "Detox_Center",
                "1060 Vignes St, Los Angeles, CA 90012",
                "213-555-0102",
                50,
                15,
            ),
        ],
    )
    connection.executemany(
        "INSERT OR IGNORE INTO caseworkers "
        "(id, full_name, role, assigned_agency, contact_phone, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                "caseworker-marcus",
                "Marcus Henderson",
                "Peer Support Specialist",
                "VOA TAY Drop-In Center",
                "213-555-0111",
                1,
            ),
        ],
    )
    connection.execute(
        "INSERT OR IGNORE INTO clinicians "
        "(id, full_name, npi_number, specialty, contact_phone) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            "clinician-karen",
            "Dr. Karen Gill, M.D.",
            "1881678364",
            "Addiction Medicine",
            "213-555-0800",
        ),
    )


def seed_database(db_path: Path = DEFAULT_DB_PATH) -> Path:
    """Create or update a database without deleting existing records."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        seed_reference_data(connection)
    return db_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    print(f"Initialized {seed_database(args.db)}")
