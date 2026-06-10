import os

import streamlit as st

from database import load_reports, load_photos
from helpers import show_recommendations, reset_incident_form
from ui import show_page_title, show_section_title


def show_command_recommendations():
    show_page_title(
        "Command Recommendations",
        "Review AI-assisted Courses of Action based on report priority."
    )

    reports_df = load_reports()

    if not reports_df.empty:
        reports_df = reports_df.sort_values(
            by="Priority Score",
            ascending=False
        )

        for _, report in reports_df.iterrows():
            show_section_title(f"{report['Barangay']} - {report['Priority']}")

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Municipality / City:** {report['Municipality / City']}")
                st.write(f"**Priority Score:** {report['Priority Score']}")
                st.write(f"**Road Status:** {report['Road Status']}")

            with col2:
                st.write(f"**Latitude:** {report['Latitude']}")
                st.write(f"**Longitude:** {report['Longitude']}")
                st.write(f"**Remarks:** {report['Remarks']}")

            st.write("**Recommended Actions:**")
            show_recommendations(st, report["Priority"])

            photos_df = load_photos(report["ID"])

            if not photos_df.empty:
                with st.expander("View Incident Photos"):
                    for _, photo in photos_df.iterrows():
                        if os.path.exists(photo["filepath"]):
                            st.image(
                                photo["filepath"],
                                caption=photo["filename"],
                                use_container_width=True
                            )

            st.divider()

        if st.button("➕ Add Another Incident Report"):
            reset_incident_form(st)
            st.rerun()

    else:
        st.warning("No reports available for command recommendations.")

        if st.button("Add Incident Report"):
            reset_incident_form(st)
            st.rerun()