import streamlit as st

from database import (
    clear_reports,
    clear_alerts,
    clear_resources,
    clear_activity_log
)
from helpers import reset_alert_form, reset_incident_form
from ui import show_page_title, show_section_title


def show_settings():
    show_page_title(
        "Settings",
        "Testing and administrative controls."
    )

    st.warning("Use these buttons only for testing.")

    show_section_title("Data Reset Controls")

    if st.button("Clear Incident Reports", use_container_width=True):
        clear_reports()
        reset_incident_form(st)
        st.success("Incident reports and photos cleared.")

    if st.button("Clear Earthquake Alerts", use_container_width=True):
        clear_alerts()
        reset_alert_form(st)
        st.success("Earthquake alerts cleared.")

    if st.button("Clear Resources", use_container_width=True):
        clear_resources()
        st.success("Resources cleared.")

    if st.button("Clear Activity Log", use_container_width=True):
        clear_activity_log()
        st.success("Activity log cleared.")

    if st.button("Clear All Data", use_container_width=True):
        clear_reports()
        clear_alerts()
        clear_resources()
        clear_activity_log()
        reset_incident_form(st)
        reset_alert_form(st)
        st.success("All data cleared.")