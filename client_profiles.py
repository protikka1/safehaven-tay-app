"""Staff demonstration for paperless case follow-up."""

from contextlib import closing
import sqlite3

import streamlit as st

from database.db import get_connection

ENTRY_STATUSES = {
    "Outreach and facility meeting": ("Planned", "Met", "Follow-up needed"),
    "Housing": ("Searching", "Facility confirmed", "Stabilizing", "Housed"),
    "Income and benefits guidance": ("Review needed", "Eligibility review", "Guidance provided"),
    "Application": ("Preparing", "Pending", "Submitted", "Decision received"),
    "Document": ("Saved",),
}


def show_client_profiles(db_path) -> None:
    st.header("Client profiles")
    st.caption("Demonstration only. Use fictional notes and sample PDFs.")
    with closing(get_connection(db_path)) as conn:
        profiles = conn.execute(
            """SELECT i.id, i.intake_code, c.full_name
               FROM intake_caseworker_assignments a
               JOIN low_barrier_intakes i ON i.id = a.intake_id
               JOIN caseworkers c ON c.id = a.caseworker_id
               ORDER BY a.assigned_at DESC, i.id DESC"""
        ).fetchall()

    if not profiles:
        st.info("Assign a caseworker to an intake to open its client profile.")
        return

    by_id = {profile["id"]: profile for profile in profiles}
    intake_id = st.selectbox("Client profile", list(by_id),
                             format_func=lambda key: by_id[key]["intake_code"])
    st.write(f"Assigned caseworker: {by_id[intake_id]['full_name']}")

    category = st.selectbox("Entry type", list(ENTRY_STATUSES), key=f"profile_type_{intake_id}")
    with st.form(f"profile_entry_{intake_id}_{category}", clear_on_submit=True):
        title = st.text_input("Facility, program, application, or document name", max_chars=120)
        status = st.selectbox("Status", ENTRY_STATUSES[category])
        notes = st.text_area("Next steps or notes", max_chars=2000)
        upload = st.file_uploader("Attach a sample PDF (optional, up to 5 MB)", type=["pdf"])
        submitted = st.form_submit_button("Save to client profile")

    if submitted:
        pdf = upload.getvalue() if upload else None
        if not title.strip():
            st.error("Enter a name for the entry.")
        elif category == "Document" and pdf is None:
            st.error("Attach a sample PDF for a document entry.")
        elif pdf is not None and (len(pdf) > 5 * 1024 * 1024 or not pdf.startswith(b"%PDF-")):
            st.error("Choose a PDF no larger than 5 MB.")
        else:
            try:
                with closing(get_connection(db_path)) as conn, conn:
                    conn.execute(
                        """INSERT INTO client_profile_entries
                           (intake_id, category, title, status, notes, pdf)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (intake_id, category, title.strip(), status, notes.strip(), pdf),
                    )
            except sqlite3.Error:
                st.error("The entry could not be saved.")
            else:
                st.success("Entry saved to the client profile.")

    with closing(get_connection(db_path)) as conn:
        entries = conn.execute(
            """SELECT id, category, title, status, notes, pdf, created_at
               FROM client_profile_entries WHERE intake_id = ? ORDER BY id DESC""",
            (intake_id,),
        ).fetchall()

    st.subheader("Profile history")
    if not entries:
        st.info("No entries have been saved for this intake.")
    for entry in entries:
        with st.expander(f"{entry['category']} · {entry['title']} · {entry['status']}"):
            st.caption(f"{entry['created_at']} UTC")
            if entry["notes"]:
                st.text(entry["notes"])
            if entry["pdf"] is not None:
                st.download_button("Download PDF", entry["pdf"],
                                   file_name=f"document-{entry['id']}.pdf",
                                   mime="application/pdf", key=f"profile_pdf_{entry['id']}")
