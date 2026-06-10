from datetime import datetime

import streamlit as st

from database import save_alert, load_alerts
from helpers import go_to_page, reset_alert_form, validate_alert
from ui import show_page_title, show_section_title


def show_earthquake_alerts():
    show_page_title(
        "Earthquake Alerts",
        "Record earthquake alert information from PHIVOLCS or authorized monitoring sources."
    )

    alert_form_key = f"alert_form_{st.session_state.alert_form_counter}"

    show_section_title("Alert Entry Form")

    with st.form(alert_form_key, clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            magnitude = st.number_input(
                "Magnitude",
                min_value=0.0,
                value=0.0,
                step=0.1
            )

            depth = st.number_input(
                "Depth in km",
                min_value=0,
                value=0
            )

        with col2:
            epicenter = st.text_input("Epicenter")

            alert_time = st.text_input(
                "Date/Time",
                value=datetime.now().strftime("%Y-%m-%d %H:%M")
            )

        remarks = st.text_area("Remarks")

        submit_alert = st.form_submit_button("Save Earthquake Alert")

    col_clear, col_dash = st.columns(2)

    with col_clear:
        if st.button("🧹 Clear Alert Input Fields", use_container_width=True):
            reset_alert_form(st)
            st.rerun()

    with col_dash:
        if st.button("Go Back to Dashboard", use_container_width=True):
            go_to_page(st, "Dashboard")
            st.rerun()

    if submit_alert:
        errors = validate_alert(
            magnitude,
            epicenter,
            depth
        )

        if errors:
            for error in errors:
                st.error(error)

        else:
            save_alert(
                magnitude,
                epicenter,
                depth,
                alert_time,
                remarks
            )

            st.success("Earthquake alert saved permanently.")

    alerts_df = load_alerts()

    if not alerts_df.empty:
        st.divider()
        show_section_title("Saved Earthquake Alerts")
        st.dataframe(alerts_df, use_container_width=True)