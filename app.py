"""SafeHaven demonstration intake. No clinical or placement authorization is performed."""
from __future__ import annotations

import hmac
from contextlib import closing
import sqlite3

import streamlit as st

from database.db import DEFAULT_DB_PATH, get_connection
from database.intake_workflow import assign_caseworker, record_request
from database.seed import seed_database
from fccw_watchdog import audit_project
from resource_hub import show_resource_hub


def staff_access_granted() -> bool:
    """Fail closed: demo requires a configured access key; not production RBAC."""
    try:
        expected = st.secrets.get("SAFEHAVEN_STAFF_ACCESS_KEY", "")
    except Exception:
        expected = ""
    if not expected:
        st.error("Staff demo is disabled until an access key is configured.")
        return False
    supplied = st.text_input("Staff demonstration access key", type="password")
    return bool(supplied) and hmac.compare_digest(supplied, str(expected))


def show_intake() -> None:
    st.caption("Demonstration intake. Use test information only.")
    st.warning("For an overdose or another medical emergency, call 911 immediately.")
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
view = st.sidebar.radio("Dashboard", ["Resource Hub", "Staff demonstration"])
if view == "Resource Hub":
    show_resource_hub(show_intake)
    st.stop()

st.header("Staff demonstration")
st.caption("Use synthetic data for intake and assignment demonstrations.")
if not staff_access_granted():
    st.stop()

seed_database(DEFAULT_DB_PATH)
queue_tab, watchdog_tab = st.tabs(["Caseworker queue", "FCCW watch"])
with queue_tab:
    notice = st.session_state.pop("assignment_notice", None)
    if notice:
        st.success(notice)
    show_caseworker_queue()

with watchdog_tab:
    st.subheader("Fourth & Central project audit")
    latitude = st.number_input("Latitude", value=34.042, format="%.6f")
    longitude = st.number_input("Longitude", value=-118.248, format="%.6f")
    affordability = st.number_input("Covenanted affordable housing (%)", min_value=0.0, max_value=100.0, value=15.0)
    audit = audit_project(latitude, longitude, affordability)
    st.metric("Status", audit.status)
    st.write(audit.reason)
