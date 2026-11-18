"""SafeHaven demonstration intake. No clinical or placement authorization is performed."""
from __future__ import annotations

import hmac
from contextlib import closing
import sqlite3

import streamlit as st

from client_profiles import show_client_profiles
from database.db import DEFAULT_DB_PATH, get_connection
from database.intake_workflow import assign_caseworker, record_request
from database.seed import seed_database
from fccw_watchdog import audit_project
from resource_hub import show_resource_hub


def access_granted(secret_name: str, label: str) -> bool:
    """Check the configured access key for this demonstration view."""
    try:
        expected = st.secrets.get(secret_name, "")
    except (FileNotFoundError, KeyError):
        expected = ""
    if not expected:
        st.info(f"{label} is unavailable until an access key is configured.")
        return False
    supplied = st.text_input(f"{label} access key", type="password", key=secret_name)
    if supplied and not hmac.compare_digest(supplied.encode(), str(expected).encode()):
        st.error("Incorrect access key.")
        return False
    return bool(supplied)


def show_intake() -> None:
    st.caption("Demonstration intake. Use test information only.")
    st.warning("For a suspected overdose or other medical emergency, call 911 now. "
               "You can get emergency screening and stabilizing treatment without insurance. "
               "Do not wait for coverage approval.")
    st.subheader("Need health coverage?")
    st.link_button("Apply for Medi-Cal through BenefitsCal", "https://benefitscal.com/")
    st.write("Ask a participating hospital or clinic whether you qualify for immediate, temporary "
             "Medi-Cal through Hospital Presumptive Eligibility.")
    st.link_button(
        "Learn about temporary Medi-Cal coverage",
        "https://www.dhcs.ca.gov/services/medi-cal-resources/medi-cal-eligibility-division/"
        "hospital-presumptive-eligibility-program/",
    )
    with st.form("intake_request"):
        age = st.selectbox("Age", ["Prefer not to say", *range(121)])
        treatment = st.checkbox("I would like help connecting with a substance use treatment clinician")
        submitted = st.form_submit_button("Submit intake")
    if submitted:
        try:
            seed_database(DEFAULT_DB_PATH)
            st.session_state.intake_result = (
                record_request(DEFAULT_DB_PATH, age if isinstance(age, int) else None, treatment),
                treatment,
            )
        except (sqlite3.Error, RuntimeError):
            st.error("The intake could not be recorded. If you need shelter help now, call 211.")
            return

    if "intake_result" not in st.session_state:
        return
    (code, route, beds), treatment = st.session_state.intake_result
    st.success(f"Intake recorded. Reference number {code}")
    st.subheader("1. Bed search")
    if route == "tay":
        for name, phone in beds:
            st.write(f"{name} · {phone}" if phone else name)
        if beds:
            st.caption("These are local records. Staff must confirm eligibility and availability.")
        else:
            st.info("No youth bed candidates were found in the local records. Call 211 for shelter navigation.")
    else:
        messages = {
            "minor_safeguarding": "A youth-serving specialist should review this intake for safe placement.",
            "adult_referral": "A navigator should review this intake for an adult housing referral.",
            "age_unknown": "A navigator should confirm the appropriate youth or adult housing pathway.",
        }
        st.info(messages[route])

    if treatment:
        st.subheader("2. Connect with a clinician")
        st.write("Call LA County’s 24/7 substance use referral line at 844-804-7500. "
                 "Ask about urgent outpatient or telehealth evaluation and medication options. "
                 "A qualified clinician evaluates treatment needs.")
        st.link_button("LA County treatment referrals",
                       "https://admin.publichealth.lacounty.gov/sapc/public/corecenter/")
    st.subheader("Caseworker follow-up")
    st.write("This intake entered the staff review queue for caseworker assignment.")


def show_caseworker_queue() -> None:
    with closing(get_connection(DEFAULT_DB_PATH)) as conn:
        pending = conn.execute(
            """SELECT id, intake_code, approximate_age, immediate_need FROM low_barrier_intakes
               WHERE status IN ('open', 'assessment', 'service_pending') ORDER BY created_at, id"""
        ).fetchall()
        workers = conn.execute(
            "SELECT id, full_name FROM caseworkers WHERE is_active = 1 ORDER BY full_name"
        ).fetchall()

    if not pending:
        st.info("No intakes are waiting for assignment.")
        return
    if not workers:
        st.info("An active caseworker is needed before an intake can be assigned.")
        return
    requests = {row["id"]: row for row in pending}
    names = {row["id"]: row["full_name"] for row in workers}
    intake_id = st.selectbox("Intake", list(requests),
                             format_func=lambda key: requests[key]["intake_code"])
    request = requests[intake_id]
    age = request["approximate_age"]
    st.write(f"Age {age if age is not None else 'unknown'} · Need {request['immediate_need']}")
    with st.form("caseworker_assignment"):
        worker_id = st.selectbox("Caseworker", list(names), format_func=names.__getitem__)
        submitted = st.form_submit_button("Assign caseworker")
    if submitted:
        try:
            assign_caseworker(DEFAULT_DB_PATH, intake_id, worker_id)
        except (ValueError, sqlite3.Error) as error:
            st.error(str(error))
        else:
            st.session_state.assignment_notice = f"Assigned {request['intake_code']} to {names[worker_id]}."
            st.rerun()


st.set_page_config(page_title="SafeHaven TAY", layout="wide")
st.title("SafeHaven TAY")
view = st.sidebar.radio("Navigation", ["Intake", "Dashboard sign-in", "Staff demonstration"])
if view == "Intake":
    st.header("Intake form")
    show_intake()
    st.stop()

if view == "Dashboard sign-in":
    st.header("Dashboard sign-in")
    if access_granted("SAFEHAVEN_DASHBOARD_ACCESS_KEY", "Dashboard"):
        show_resource_hub()
    st.stop()

st.header("Staff demonstration")
st.caption("Use synthetic data for intake and assignment demonstrations.")
if not access_granted("SAFEHAVEN_STAFF_ACCESS_KEY", "Staff"):
    st.stop()

seed_database(DEFAULT_DB_PATH)
queue_tab, profiles_tab, watchdog_tab = st.tabs(["Caseworker queue", "Client profiles", "FCCW watch"])
with queue_tab:
    notice = st.session_state.pop("assignment_notice", None)
    if notice:
        st.success(notice)
    show_caseworker_queue()

with profiles_tab:
    show_client_profiles(DEFAULT_DB_PATH)

with watchdog_tab:
    st.subheader("Fourth & Central project audit")
    latitude = st.number_input("Latitude", value=34.042, format="%.6f")
    longitude = st.number_input("Longitude", value=-118.248, format="%.6f")
    affordability = st.number_input("Covenanted affordable housing (%)", min_value=0.0, max_value=100.0, value=15.0)
    audit = audit_project(latitude, longitude, affordability)
    st.metric("Status", audit.status)
    st.write(audit.reason)
