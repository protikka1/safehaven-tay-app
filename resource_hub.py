"""Public resource navigation for Los Angeles transitional-age youth."""

from contextlib import closing
import sqlite3

import streamlit as st

from database.db import DEFAULT_DB_PATH

SHELTER_URL = "https://211la.org/year-round-shelter"
TREATMENT_URL = "https://sapccis.ph.lacounty.gov/sbat/"
RESOURCES = {
    "Housing and basic needs": (
        ("211 LA shelter navigation", SHELTER_URL,
         "Call 211 for help finding shelter and basic-needs services. Ask about youth programs."),
    ),
    "Telehealth and opioid treatment": (
        ("LA County treatment directory", TREATMENT_URL,
         "Call the 24/7 county referral line at 844-804-7500. Ask about outpatient "
         "telehealth, a clinician evaluation for medications for opioid use disorder, "
         "and appointment availability."),
    ),
    "Clinics and pharmacies": (
        ("LA County Health Services", "https://dhs.lacounty.gov/", "Find county clinical services."),
        ("Medi-Cal Rx", "https://medi-calrx.dhcs.ca.gov/home/",
         "Use Find a Pharmacy to locate participating pharmacies. Call to confirm "
         "pharmacy counter hours and medication stock before traveling."),
    ),
    "Health coverage and benefits": (
        ("BenefitsCal", "https://benefitscal.com/", "Apply for Medi-Cal through your county."),
        ("Covered California", "https://www.coveredca.com/",
         "Apply for Medi-Cal or check marketplace coverage options."),
    ),
    "Mental health": (
        ("LA County Department of Mental Health", "https://dmh.lacounty.gov/",
         "Find county mental health services and support."),
    ),
}


def load_facilities():
    """Read facility contact details without opening or creating a writable database."""
    if not DEFAULT_DB_PATH.is_file():
        return []
    uri = DEFAULT_DB_PATH.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        return connection.execute(
            "SELECT name, facility_type, street_address, contact_phone "
            "FROM facilities WHERE lower(name) NOT LIKE 'example%' ORDER BY name"
        ).fetchall()


def show_resource_hub() -> None:
    st.header("Resource Hub")
    st.caption("Housing, treatment and benefits for Los Angeles youth ages 18–24.")
    st.write("Browse without signing in or sharing personal information.")
    resources, directory, navigator = st.tabs(
        ["Find resources", "Local directory", "Talk to a navigator"]
    )

    with resources:
        category = st.selectbox("What do you need?", list(RESOURCES))
        for title, url, description in RESOURCES[category]:
            st.link_button(title, url)
            st.write(description)

    with directory:
        try:
            facilities = load_facilities()
        except sqlite3.Error:
            st.info("The local directory is temporarily unavailable. Use Find resources for provider links.")
        else:
            if not facilities:
                st.info("Use Find resources for provider links while the local directory is being populated.")
            for name, kind, address, phone in facilities:
                with st.expander(name):
                    st.text(kind.replace("_", " "))
                    st.text(address)
                    if phone:
                        st.text(phone)
            if facilities:
                st.caption("Contact the provider to confirm hours, eligibility and availability.")

    with navigator:
        st.write("**Call 211** for shelter and basic needs. Ask about a youth navigator or caseworker.")
        st.link_button("Open 211 LA", SHELTER_URL)
        st.write("**Call 844-804-7500** for 24/7 LA County substance-use screening and referrals.")
        st.link_button("Open LA County treatment directory", TREATMENT_URL)
        st.caption("These services handle their own referrals and follow-up. SafeHaven provides the contact information.")
