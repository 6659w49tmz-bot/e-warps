import os

import streamlit as st
from streamlit_geolocation import streamlit_geolocation

from database import save_report, load_reports, load_photos
from helpers import (
    calculate_priority,
    show_recommendations,
    go_to_page,
    reset_incident_form,
    geocode_location,
    validate_incident_report
)
from ui import show_page_title, show_section_title


def show_incident_reports():
    show_page_title(
        "Incident Reports",
        "Submit field reports, attach photos, and record location data."
    )

    show_section_title("Location Capture")

    location_method = st.radio(
        "Select Location Method",
        [
            "Use Current Device Location",
            "Search by Barangay / City",
            "Manual Coordinates"
        ],
        horizontal=True
    )

    if location_method == "Use Current Device Location":
        st.info(
            "Click the geolocation button below and allow location permission when the browser asks."
        )

        location = streamlit_geolocation()

        if location:
            latitude_result = location.get("latitude")
            longitude_result = location.get("longitude")

            if latitude_result is not None and longitude_result is not None:
                st.session_state.current_latitude = float(latitude_result)
                st.session_state.current_longitude = float(longitude_result)

                st.success(
                    f"Current device location captured: "
                    f"{st.session_state.current_latitude:.6f}, "
                    f"{st.session_state.current_longitude:.6f}"
                )

    elif location_method == "Search by Barangay / City":
        st.info(
            "Type the barangay and city/municipality, then click Find Coordinates."
        )

        search_col1, search_col2 = st.columns(2)

        with search_col1:
            search_barangay = st.text_input("Barangay / Location Name for Search")

        with search_col2:
            search_municipality = st.text_input("Municipality / City for Search")

        if st.button("📍 Find Coordinates from Location Name", use_container_width=True):
            lat, lon, address = geocode_location(
                search_barangay,
                search_municipality
            )

            if lat is not None and lon is not None:
                st.session_state.current_latitude = lat
                st.session_state.current_longitude = lon

                st.success(f"Coordinates found: {lat:.6f}, {lon:.6f}")
                st.write(f"**Matched Address:** {address}")
            else:
                st.error(
                    "No coordinates found. Try adding province/region or use manual coordinates."
                )

    else:
        st.info("Enter the coordinates manually in the form below.")

    st.divider()

    show_section_title("Field Report Form")

    form_key = f"incident_form_{st.session_state.incident_form_counter}"

    with st.form(form_key, clear_on_submit=True):
        col_a, col_b = st.columns(2)

        with col_a:
            barangay = st.text_input("Barangay")

        with col_b:
            municipality = st.text_input("Municipality / City")

        coord_col1, coord_col2 = st.columns(2)

        with coord_col1:
            latitude = st.number_input(
                "Latitude",
                value=float(st.session_state.current_latitude),
                format="%.6f"
            )

        with coord_col2:
            longitude = st.number_input(
                "Longitude",
                value=float(st.session_state.current_longitude),
                format="%.6f"
            )

        st.divider()

        impact_col1, impact_col2 = st.columns(2)

        with impact_col1:
            casualties = st.number_input(
                "Number of Casualties",
                min_value=0,
                value=0
            )

            trapped = st.number_input(
                "Number of Trapped Persons",
                min_value=0,
                value=0
            )

        with impact_col2:
            injured = st.number_input(
                "Number of Injured Persons",
                min_value=0,
                value=0
            )

            damaged_buildings = st.number_input(
                "Damaged Buildings",
                min_value=0,
                value=0
            )

        road_status = st.selectbox(
            "Road Status",
            [
                "Passable",
                "Partially Blocked",
                "Blocked"
            ]
        )

        uploaded_photos = st.file_uploader(
            "Upload Incident Photos",
            type=[
                "jpg",
                "jpeg",
                "png"
            ],
            accept_multiple_files=True
        )

        remarks = st.text_area("Remarks")

        submit_report = st.form_submit_button("Submit Report")

    col_clear, col_dash = st.columns(2)

    with col_clear:
        if st.button("🧹 Clear Report Input Fields", use_container_width=True):
            reset_incident_form(st)
            st.rerun()

    with col_dash:
        if st.button("Go Back to Dashboard", use_container_width=True):
            go_to_page(st, "Dashboard")
            st.rerun()

    if submit_report:
        errors = validate_incident_report(
            barangay,
            municipality,
            casualties,
            injured,
            trapped,
            damaged_buildings,
            remarks,
            uploaded_photos
        )

        if errors:
            for error in errors:
                st.error(error)

        else:
            score, priority = calculate_priority(
                casualties,
                injured,
                trapped,
                damaged_buildings,
                road_status
            )

            report_id = save_report(
                barangay,
                municipality,
                latitude,
                longitude,
                casualties,
                injured,
                trapped,
                damaged_buildings,
                road_status,
                score,
                priority,
                remarks,
                uploaded_photos
            )

            st.success("Incident report saved permanently.")

            show_section_title("Submitted Report")

            submitted_df = load_reports()
            submitted_df = submitted_df[submitted_df["ID"] == report_id]

            st.dataframe(submitted_df, use_container_width=True)

            photos_df = load_photos(report_id)

            if not photos_df.empty:
                show_section_title("Uploaded Photos")

                for _, photo in photos_df.iterrows():
                    if os.path.exists(photo["filepath"]):
                        st.image(
                            photo["filepath"],
                            caption=photo["filename"],
                            use_container_width=True
                        )

            show_section_title("AI-Assisted Command Recommendations")
            show_recommendations(st, priority)

            st.divider()

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("➕ Submit Another Incident Report", use_container_width=True):
                    reset_incident_form(st)
                    st.rerun()

            with col2:
                if st.button("🚨 View Prioritization", use_container_width=True):
                    go_to_page(st, "Prioritization")
                    st.rerun()

            with col3:
                if st.button("🗺️ View GIS Map", use_container_width=True):
                    go_to_page(st, "GIS Map")
                    st.rerun()