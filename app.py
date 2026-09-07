"""SafeHaven TAY care coordination and FCCW status dashboard."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

from database.seed import DEFAULT_DB_PATH, seed_database
from fccw_watchdog import audit_project


TODAY = datetime.now(timezone.utc).date()


def db_connection() -> sqlite3.Connection:
    """Open the seeded local database with foreign-key enforcement enabled."""
    seed_database(DEFAULT_DB_PATH)
    connection = sqlite3.connect(DEFAULT_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def load_dashboard_data() -> tuple[
    list[sqlite3.Row], list[sqlite3.Row], list[sqlite3.Row]
]:
    with db_connection() as connection:
        facilities = connection.execute(
            "SELECT name, facility_type, total_capacity, available_beds "
            "FROM facilities ORDER BY name"
        ).fetchall()
        placements = connection.execute(
            "SELECT y.alias, f.name AS facility, p.placement_type, "
            "p.status, p.start_date FROM program_placements p "
            "JOIN youth_profiles y ON p.youth_id = y.id "
            "JOIN facilities f ON p.facility_id = f.id "
            "ORDER BY p.start_date DESC"
        ).fetchall()
        mats = connection.execute(
            "SELECT y.alias, m.medication_name, m.dosage_instructions, "
            "c.full_name AS doctor, m.adherence_status "
            "FROM mat_prescriptions m "
            "JOIN youth_profiles y ON m.youth_id = y.id "
            "JOIN clinicians c ON m.prescribing_clinician_id = c.id "
            "ORDER BY m.start_date DESC"
        ).fetchall()
    return facilities, placements, mats


def create_atomic_intake(
    alias: str,
    first_name: str,
    last_name: str,
    date_of_birth: date,
    phone: str,
    primary_substance: str,
    overdose_count: int,
) -> str:
    """Create all intake records in one transaction."""
    with db_connection() as connection:
        facility = connection.execute(
            "SELECT id, name, available_beds FROM facilities "
            "WHERE facility_type IN ('Substance_Use_Hub', 'Detox_Center') "
            "AND available_beds > 0 ORDER BY available_beds DESC LIMIT 1"
        ).fetchone()
        clinician = connection.execute(
            "SELECT id FROM clinicians ORDER BY created_at LIMIT 1"
        ).fetchone()
        caseworker = connection.execute(
            "SELECT id FROM caseworkers WHERE is_active = 1 "
            "ORDER BY created_at LIMIT 1"
        ).fetchone()
        if not facility:
            raise ValueError(
                "No detox or substance-use facility has an available bed."
            )
        if not clinician or not caseworker:
            raise ValueError(
                "A clinician and active caseworker are required for booking."
            )
        youth_id = str(uuid.uuid4())
        connection.execute(
            "INSERT INTO youth_profiles "
            "(id, alias, first_name, last_name, date_of_birth, "
            "safelink_phone_number) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                youth_id,
                alias.strip(),
                first_name.strip() or None,
                last_name.strip() or None,
                date_of_birth.isoformat(),
                phone.strip() or None,
            ),
        )
        connection.execute(
            "INSERT INTO assessments "
            "(id, youth_id, assessor_id, assessment_type, primary_substance, "
            "overdose_history_count, housing_status_at_intake) "
            "VALUES (?, ?, ?, 'SUD_Screening', ?, ?, 'Unsheltered')",
            (
                str(uuid.uuid4()),
                youth_id,
                caseworker["id"],
                primary_substance,
                overdose_count,
            ),
        )
        connection.execute(
            "UPDATE facilities SET available_beds = available_beds - 1 "
            "WHERE id = ?",
            (facility["id"],),
        )
        connection.execute(
            "INSERT INTO program_placements "
            "(id, youth_id, facility_id, placement_type, start_date, status) "
            "VALUES (?, ?, ?, 'Detox_Stay', ?, 'Enrolled')",
            (
                str(uuid.uuid4()),
                youth_id,
                facility["id"],
                TODAY.isoformat(),
            ),
        )
        connection.execute(
            "INSERT INTO mat_prescriptions "
            "(id, youth_id, prescribing_clinician_id, medication_name, "
            "dosage_instructions, start_date, dispensing_facility_id) "
            "VALUES (?, ?, ?, 'Buprenorphine', ?, ?, ?)",
            (
                str(uuid.uuid4()),
                youth_id,
                clinician["id"],
                "8mg sublingual strip daily under peer observation",
                TODAY.isoformat(),
                facility["id"],
            ),
        )
    return f"{alias.strip()} booked at {facility['name']}"


st.set_page_config(page_title="SafeHaven TAY", page_icon="+", layout="wide")
st.title("SafeHaven TAY")
st.caption(
    "Low-barrier recovery intake, care coordination, and community monitoring"
)

facilities, placements, mats = load_dashboard_data()
intake_tab, watchdog_tab = st.tabs(["Recovery intake", "FCCW watch"])

with intake_tab:
    availability, intake = st.columns(2)
    with availability:
        st.subheader("Facility availability")
        if facilities:
            for facility in facilities:
                beds = facility["available_beds"]
                total = facility["total_capacity"] or 0
                status = "Available" if beds > 0 else "Fully booked"
                st.write(
                    f"**{facility['name']}** | "
                    f"{facility['facility_type'].replace('_', ' ')} "
                    f"| {beds}/{total} beds | {status}"
                )
        else:
            st.info("No facilities have been configured yet.")

    with intake:
        st.subheader("One-click recovery intake")
        st.info("A street alias is enough to begin. Legal names are optional.")
        max_birth = TODAY - timedelta(days=18 * 365)
        min_birth = TODAY - timedelta(days=25 * 365) + timedelta(days=1)
        with st.form("quick_intake_form", clear_on_submit=True):
            alias = st.text_input("Street alias", max_chars=80)
            first_name = st.text_input("First name (optional)")
            last_name = st.text_input("Last name (optional)")
            date_of_birth = st.date_input(
                "Date of birth (ages 18-24)",
                value=max_birth,
                min_value=min_birth,
                max_value=max_birth,
            )
            phone = st.text_input("SafeLink phone (optional)")
            substance = st.selectbox(
                "Primary substance",
                [
                    "Opioids/Fentanyl",
                    "Alcohol",
                    "Stimulants",
                    "Benzodiazepines",
                    "Multiple",
                ],
            )
            overdose_count = st.number_input(
                "Overdose history count", 0, 20, 0
            )
            submitted = st.form_submit_button(
                "Book and initiate MAT treatment"
            )
        if submitted:
            if not alias.strip():
                st.error("An alias is required.")
            else:
                try:
                    st.success(
                        create_atomic_intake(
                            alias,
                            first_name,
                            last_name,
                            date_of_birth,
                            phone,
                            substance,
                            overdose_count,
                        )
                    )
                    st.rerun()
                except ValueError as error:
                    st.warning(str(error))
                except sqlite3.IntegrityError:
                    st.error(
                        "The intake could not be saved because the database "
                        "rejected it."
                    )

    st.divider()
    placements_column, mats_column = st.columns(2)
    with placements_column:
        st.subheader("Active placements")
        for placement in placements:
            st.write(
                f"**{placement['alias']}** | {placement['facility']} | "
                f"{placement['placement_type']} | {placement['start_date']}"
            )
        if not placements:
            st.info("No active placements.")
    with mats_column:
        st.subheader("Active MAT treatments")
        for mat in mats:
            st.write(
                f"**{mat['alias']}** | {mat['medication_name']} | "
                f"{mat['doctor']} | {mat['adherence_status']}"
            )
        if not mats:
            st.info("No active MAT treatments.")

with watchdog_tab:
    st.subheader("Fourth & Central project audit")
    latitude = st.number_input("Latitude", value=34.042, format="%.6f")
    longitude = st.number_input("Longitude", value=-118.248, format="%.6f")
    affordability = st.number_input(
        "Covenanted affordable housing (%)",
        min_value=0.0,
        max_value=100.0,
        value=15.0,
    )
    audit = audit_project(latitude, longitude, affordability)
    st.metric("Status", audit.status)
    st.write(audit.reason)

st.caption(f"Local database: {Path(DEFAULT_DB_PATH)}")
