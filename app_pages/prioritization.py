import streamlit as st

from database import load_reports
from helpers import reset_incident_form
from ui import show_page_title, show_section_title, show_status_legend


def show_prioritization():
    show_page_title(
        "Rescue Prioritization",
        "Rank affected areas based on weighted urgency scoring."
    )

    show_status_legend()

    st.divider()

    reports_df = load_reports()

    if not reports_df.empty:
        reports_df = reports_df.sort_values(
            by="Priority Score",
            ascending=False
        )

        show_section_title("Prioritized Incident Reports")

        st.dataframe(reports_df, use_container_width=True)

        st.divider()

        top = reports_df.iloc[0]

        show_section_title("Top Priority Area")
        st.error(f"{top['Barangay']} - {top['Priority']}")
        st.metric("Priority Score", int(top["Priority Score"]))

        if st.button("➕ Add Another Incident Report"):
            reset_incident_form(st)
            st.rerun()

    else:
        st.warning("No reports available for prioritization.")

        if st.button("Add Incident Report"):
            reset_incident_form(st)
            st.rerun()