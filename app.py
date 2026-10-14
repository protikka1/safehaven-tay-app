"""SafeHaven demonstration intake. No clinical or placement authorization is performed."""
from __future__ import annotations

import hmac
import secrets
import sqlite3
from pathlib import Path

import streamlit as st

from database.age_routing import age_route
from database.db import DEFAULT_DB_PATH, get_connection
from database.seed import seed_database
from fccw_watchdog import audit_project


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


def record_request(alias: str, approximate_age: int | None, immediate_need: str) -> tuple[str, str]:
    """Record an initial request without reserving beds or issuing prescriptions."""
    route = age_route(approximate_age)
    code = "SH-" + secrets.token_hex(12).upper()
    with get_connection(DEFAULT_DB_PATH) as conn:
        conn.execute(
            """INSERT INTO low_barrier_intakes
               (intake_code, street_alias, approximate_age, immediate_need,
                intake_method, status)
               VALUES (?, ?, ?, ?, 'web', 'open')""",
            (code, alias.strip() or None, approximate_age, immediate_need),
        )
    return code, route


st.set_page_config(page_title="SafeHaven TAY | Staff Demo", layout="wide")
st.title("SafeHaven TAY — Staff demonstration")
st.caption("Synthetic-data demonstration only. Not approved for real patient intake or placement.")
if not staff_access_granted():
    st.stop()

seed_database(DEFAULT_DB_PATH)
intake_tab, watchdog_tab = st.tabs(["Low-barrier request", "FCCW watch"])
with intake_tab:
    st.info("Requests can be recorded without legal name, birth date, phone, or clinical disclosures.")
    with st.form("intake_request", clear_on_submit=True):
        alias = st.text_input("Street alias (optional)", max_chars=80)
        age_known = st.checkbox("Approximate age known")
        age = st.number_input("Approximate age", min_value=0, max_value=120, value=18) if age_known else None
        need = st.selectbox("Immediate need", ["shelter", "detox", "medical", "recovery", "miscellaneous"])
        submitted = st.form_submit_button("Record request — no bed booking")
    if submitted:
        try:
            code, route = record_request(alias, int(age) if age is not None else None, need)
            st.success(f"Request recorded: {code}")
            if route == "minor_safeguarding":
                st.warning("Minor: refer promptly to qualified child-serving personnel. No adult-shelter placement.")
            elif route == "age_unknown":
                st.warning("Age unknown: protected age and safety assessment required before any placement.")
            elif route == "adult_referral":
                st.info("Adult referral pathway: human service review required.")
            else:
                st.info("TAY pathway: staff assessment and provider acceptance required before any placement.")
            st.caption("This demonstration does not contact emergency services or send referrals.")
        except (ValueError, sqlite3.Error) as error:
            st.error(f"Request could not be recorded: {error}")

with watchdog_tab:
    st.subheader("Fourth & Central project audit")
    latitude = st.number_input("Latitude", value=34.042, format="%.6f")
    longitude = st.number_input("Longitude", value=-118.248, format="%.6f")
    affordability = st.number_input("Covenanted affordable housing (%)", min_value=0.0, max_value=100.0, value=15.0)
    audit = audit_project(latitude, longitude, affordability)
    st.metric("Status", audit.status)
    st.write(audit.reason)
