"""SafeHaven application dashboard."""

from pathlib import Path

import streamlit as st

FORMS = Path(__file__).resolve().parent / "docs" / "forms"
APPLICATIONS = (
    ("Medi-Cal application", "https://benefitscal.com/"),
    ("Covered California application", "https://www.coveredca.com/"),
    ("CalFresh application", "https://dpss.lacounty.gov/en/food/calfresh.html"),
    ("Housing application information", "https://hacla.org/en/about-public-housing/public-housing-applicants"),
    ("Social Security disability application (SSDI or SSI)", "https://www.ssa.gov/apply"),
)
DOCUMENTS = (
    ("CalWORKs and child support forms", "skid-row-calworks-child-support-intake-forms.pdf"),
    ("Eviction prevention and medical care playbook", "skid-row-eviction-and-medical-forms.pdf"),
    ("Family preservation and legal forms", "skid-row-preventative-legal-forms.pdf"),
)


def show_resource_hub(show_intake) -> None:
    st.header("Resource Hub")
    intake, applications, documents, involvement = st.tabs(
        ["Intake form", "Applications", "PDF documents", "Volunteer and support"]
    )
    with intake:
        show_intake()
    with applications:
        for title, url in APPLICATIONS:
            st.link_button(title, url)
    with documents:
        for title, filename in DOCUMENTS:
            path = FORMS / filename
            if path.is_file():
                st.download_button(title, path.read_bytes(), file_name=filename, mime="application/pdf")
    with involvement:
        st.subheader("Volunteer")
        st.write("Help with outreach, resource updates, or community events.")
        st.subheader("Support SafeHaven")
        st.write("Community groups can help with supplies, outreach, or referral partnerships.")
        st.caption("Volunteer and supporter registration is pending a project contact.")
