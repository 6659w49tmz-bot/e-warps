import re
import streamlit as st

from database import save_alert, load_alerts, log_activity
from helpers import (
    validate_alert,
    reset_alert_form
)
from ui import show_page_title, show_section_title


# =========================
# HELPER FUNCTIONS
# =========================
def get_alert_value(alert, possible_keys, default=""):
    """
    Gets alert value even if the column name differs between
    manual alerts, automated alerts, or database dataframe mapping.
    """
    for key in possible_keys:
        if key in alert:
            value = alert.get(key)

            if value is not None and str(value).strip() != "":
                return value

    return default


def extract_coordinates_from_remarks(remarks):
    if not remarks:
        return None, None

    match = re.search(
        r"Coordinates:\s*([-+]?\d+\.\d+),\s*([-+]?\d+\.\d+)",
        str(remarks)
    )

    if not match:
        return None, None

    latitude = float(match.group(1))
    longitude = float(match.group(2))

    return latitude, longitude


def create_incident_draft_from_alert(alert):
    magnitude = get_alert_value(
        alert,
        ["Magnitude", "magnitude"],
        ""
    )

    epicenter = get_alert_value(
        alert,
        ["Epicenter", "epicenter", "Location", "location"],
        ""
    )

    depth = get_alert_value(
        alert,
        ["Depth", "depth"],
        ""
    )

    alert_time = get_alert_value(
        alert,
        [
            "Alert Time",
            "Alert Date/Time",
            "Date and Time",
            "Date/Time",
            "alert_time",
            "created_at",
            "Created At"
        ],
        ""
    )

    remarks = get_alert_value(
        alert,
        ["Remarks", "remarks"],
        ""
    )

    latitude, longitude = extract_coordinates_from_remarks(remarks)

    st.session_state.incident_barangay = str(epicenter)
    st.session_state.incident_municipality = "For validation"

    if latitude is not None and longitude is not None:
        st.session_state.current_latitude = latitude
        st.session_state.current_longitude = longitude
        st.session_state.map_pin_latitude = latitude
        st.session_state.map_pin_longitude = longitude

    st.session_state.incident_prefill_remarks = (
        f"Incident report draft created from earthquake alert.\n\n"
        f"Earthquake Alert Details:\n"
        f"Magnitude: {magnitude}\n"
        f"Epicenter: {epicenter}\n"
        f"Depth: {depth} km\n"
        f"Alert Date/Time: {alert_time}\n"
        f"Alert Remarks: {remarks}\n\n"
        f"Field responder must validate actual casualties, injuries, trapped persons, "
        f"building damage, road condition, and other incident details."
    )

    st.session_state.selected_location_method = "Manual Coordinates"
    st.session_state.pending_page = "Incident Reports"

    log_activity(
        "Incident Draft Created",
        f"Created incident report draft from earthquake alert: M{magnitude} | {epicenter}"
    )


# =========================
# MAIN PAGE
# =========================
def show_earthquake_alerts():
    show_page_title(
        "Earthquake Alerts",
        "Encode, view, and convert earthquake alerts into incident report drafts."
    )

    form_key = f"earthquake_alert_form_{st.session_state.alert_form_counter}"

    show_section_title("Add Earthquake Alert")

    with st.form(form_key):
        col1, col2, col3 = st.columns(3)

        with col1:
            magnitude = st.number_input(
                "Magnitude",
                min_value=0.0,
                max_value=10.0,
                step=0.1,
                format="%.1f"
            )

        with col2:
            depth = st.number_input(
                "Depth (km)",
                min_value=0.0,
                step=1.0,
                format="%.1f"
            )

        with col3:
            alert_time = st.text_input(
                "Alert Date/Time",
                placeholder="Example: 2026-06-11 10:30 AM"
            )

        epicenter = st.text_input(
            "Epicenter / Location",
            placeholder="Example: Western Bicutan, Taguig"
        )

        remarks = st.text_area(
            "Remarks",
            placeholder="Add source, coordinates, alert notes, or other relevant details."
        )

        submitted = st.form_submit_button(
            "Save Earthquake Alert",
            use_container_width=True
        )

    if submitted:
        validation_errors = validate_alert(
            magnitude,
            epicenter,
            depth,
            alert_time
        )

        if validation_errors:
            for error in validation_errors:
                st.error(error)

        else:
            save_alert(
                magnitude,
                epicenter,
                depth,
                alert_time,
                remarks
            )

            log_activity(
                "Earthquake Alert Saved",
                f"M{magnitude} | {epicenter}"
            )

            st.success("Earthquake alert saved successfully.")
            reset_alert_form(st)
            st.rerun()

    st.divider()

    show_section_title("Saved Earthquake Alerts")

    alerts_df = load_alerts()

    if alerts_df.empty:
        st.info("No earthquake alerts available yet.")
        return

    if "ID" in alerts_df.columns:
        sorted_alerts_df = alerts_df.sort_values(
            by="ID",
            ascending=False
        )
    else:
        sorted_alerts_df = alerts_df

    for index, alert in sorted_alerts_df.iterrows():
        alert_dict = alert.to_dict()

        alert_id = get_alert_value(
            alert_dict,
            ["ID", "id"],
            index
        )

        magnitude = get_alert_value(
            alert_dict,
            ["Magnitude", "magnitude"],
            "N/A"
        )

        epicenter = get_alert_value(
            alert_dict,
            ["Epicenter", "epicenter", "Location", "location"],
            "Unknown location"
        )

        depth = get_alert_value(
            alert_dict,
            ["Depth", "depth"],
            "N/A"
        )

        alert_time = get_alert_value(
            alert_dict,
            [
                "Alert Time",
                "Alert Date/Time",
                "Date and Time",
                "Date/Time",
                "alert_time",
                "Created At",
                "created_at"
            ],
            "No date/time available"
        )

        remarks = get_alert_value(
            alert_dict,
            ["Remarks", "remarks"],
            ""
        )

        with st.expander(
            f"M{magnitude} | {epicenter} | {alert_time}",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Magnitude", magnitude)

            with col2:
                if str(depth) == "N/A":
                    st.metric("Depth", "N/A")
                else:
                    st.metric("Depth", f"{depth} km")

            with col3:
                st.metric("Alert ID", alert_id)

            st.write("**Epicenter / Location:**")
            st.write(epicenter)

            st.write("**Alert Date/Time:**")
            st.write(alert_time)

            st.write("**Remarks:**")
            st.write(remarks if remarks else "No remarks provided.")

            latitude, longitude = extract_coordinates_from_remarks(remarks)

            if latitude is not None and longitude is not None:
                st.caption(
                    f"Detected Coordinates: {latitude:.6f}, {longitude:.6f}"
                )
            else:
                st.caption(
                    "No coordinates detected in remarks. Incident draft can still be created, "
                    "but coordinates must be validated manually."
                )

            if st.button(
                "Create Incident Report from this Alert",
                key=f"create_incident_from_alert_{alert_id}",
                use_container_width=True
            ):
                create_incident_draft_from_alert(alert_dict)
                st.success("Incident report draft created from alert.")
                st.rerun()