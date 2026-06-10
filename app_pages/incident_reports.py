import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from database import save_report, log_activity
from helpers import (
    calculate_priority,
    validate_incident_report,
    reset_incident_form
)
from ui import show_page_title, show_section_title


# =========================
# REVERSE GEOCODING
# =========================
def reverse_geocode_location(latitude, longitude):
    try:
        geolocator = Nominatim(user_agent="e-warps-capstone")

        location = geolocator.reverse(
            f"{latitude}, {longitude}",
            exactly_one=True,
            timeout=10,
            language="en"
        )

        if not location:
            return "", "", ""

        address = location.raw.get("address", {})

        barangay_area = (
            address.get("suburb")
            or address.get("neighbourhood")
            or address.get("quarter")
            or address.get("city_district")
            or address.get("village")
            or address.get("hamlet")
            or address.get("road")
            or ""
        )

        municipality_city = (
            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or address.get("county")
            or ""
        )

        full_address = location.address

        return barangay_area, municipality_city, full_address

    except (GeocoderTimedOut, GeocoderServiceError):
        return "", "", ""

    except Exception:
        return "", "", ""


def show_incident_reports():
    show_page_title(
        "Incident Reports",
        "Encode earthquake-related damage, casualty, and rescue information."
    )

    form_key = f"incident_report_form_{st.session_state.incident_form_counter}"

    if "map_pin_latitude" not in st.session_state:
        st.session_state.map_pin_latitude = 14.520000

    if "map_pin_longitude" not in st.session_state:
        st.session_state.map_pin_longitude = 121.050000

    if "selected_location_method" not in st.session_state:
        st.session_state.selected_location_method = "Manual Coordinates"

    if "incident_barangay" not in st.session_state:
        st.session_state.incident_barangay = ""

    if "incident_municipality" not in st.session_state:
        st.session_state.incident_municipality = ""

    if "incident_full_address" not in st.session_state:
        st.session_state.incident_full_address = ""

    show_section_title("Location Input Method")

    location_method = st.radio(
        "Choose how to set the incident location",
        [
            "Use Current Device Location",
            "Select Location from Map Pin",
            "Manual Coordinates"
        ],
        horizontal=False,
        key="selected_location_method"
    )

    if location_method == "Use Current Device Location":
        st.info(
            "Use this if the device browser allows location access. "
            "On iPhone, open the app directly in Safari and allow Precise Location."
        )

        try:
            from streamlit_geolocation import streamlit_geolocation

            location = streamlit_geolocation()

            if location:
                latitude_from_device = location.get("latitude")
                longitude_from_device = location.get("longitude")

                if latitude_from_device is not None and longitude_from_device is not None:
                    st.session_state.current_latitude = float(latitude_from_device)
                    st.session_state.current_longitude = float(longitude_from_device)

                    barangay_area, municipality_city, full_address = reverse_geocode_location(
                        st.session_state.current_latitude,
                        st.session_state.current_longitude
                    )

                    if barangay_area:
                        st.session_state.incident_barangay = barangay_area

                    if municipality_city:
                        st.session_state.incident_municipality = municipality_city

                    if full_address:
                        st.session_state.incident_full_address = full_address

                    st.success("Device location captured successfully.")

                    st.write(
                        f"Latitude: `{st.session_state.current_latitude:.6f}`"
                    )
                    st.write(
                        f"Longitude: `{st.session_state.current_longitude:.6f}`"
                    )

                    if st.session_state.incident_full_address:
                        st.caption(
                            f"Detected address: {st.session_state.incident_full_address}"
                        )

                else:
                    st.warning("Location permission may not have been granted yet.")
            else:
                st.warning("No device location received yet.")

        except Exception as error:
            st.warning("Device location is not available on this browser/device.")
            st.caption(str(error))

    elif location_method == "Select Location from Map Pin":
        st.info(
            "Tap or click the incident location on the map, then click "
            "**Use Selected Map Pin**."
        )

        map_center_latitude = st.session_state.current_latitude
        map_center_longitude = st.session_state.current_longitude

        if map_center_latitude == 0 or map_center_longitude == 0:
            map_center_latitude = st.session_state.map_pin_latitude
            map_center_longitude = st.session_state.map_pin_longitude

        incident_map = folium.Map(
            location=[
                map_center_latitude,
                map_center_longitude
            ],
            zoom_start=14
        )

        folium.Marker(
            [
                st.session_state.map_pin_latitude,
                st.session_state.map_pin_longitude
            ],
            popup="Selected Incident Location",
            tooltip="Selected Incident Location"
        ).add_to(incident_map)

        map_data = st_folium(
            incident_map,
            height=450,
            use_container_width=True
        )

        if map_data and map_data.get("last_clicked"):
            clicked_latitude = map_data["last_clicked"]["lat"]
            clicked_longitude = map_data["last_clicked"]["lng"]

            st.session_state.map_pin_latitude = float(clicked_latitude)
            st.session_state.map_pin_longitude = float(clicked_longitude)

            st.success("Map pin selected.")

            st.write(
                f"Selected Latitude: `{st.session_state.map_pin_latitude:.6f}`"
            )
            st.write(
                f"Selected Longitude: `{st.session_state.map_pin_longitude:.6f}`"
            )

        if st.button("Use Selected Map Pin", use_container_width=True):
            st.session_state.current_latitude = st.session_state.map_pin_latitude
            st.session_state.current_longitude = st.session_state.map_pin_longitude

            barangay_area, municipality_city, full_address = reverse_geocode_location(
                st.session_state.current_latitude,
                st.session_state.current_longitude
            )

            if barangay_area:
                st.session_state.incident_barangay = barangay_area

            if municipality_city:
                st.session_state.incident_municipality = municipality_city

            if full_address:
                st.session_state.incident_full_address = full_address

            st.success("Map pin location applied to this incident report.")

            if full_address:
                st.info(f"Detected address: {full_address}")
            else:
                st.warning(
                    "Coordinates were applied, but the address could not be detected. "
                    "You may manually type the barangay and city."
                )

            st.rerun()

    else:
        st.info("Manually input the latitude and longitude of the incident location.")

    st.divider()

    show_section_title("Incident Report Form")

    with st.form(form_key):
        barangay = st.text_input(
            "Barangay / Area",
            value=st.session_state.incident_barangay
        )

        municipality = st.text_input(
            "Municipality / City",
            value=st.session_state.incident_municipality
        )

        if st.session_state.incident_full_address:
            st.caption(
                f"Detected address: {st.session_state.incident_full_address}"
            )

        st.markdown("#### Coordinates")

        latitude = st.number_input(
            "Latitude",
            min_value=-90.000000,
            max_value=90.000000,
            value=float(st.session_state.current_latitude),
            format="%.6f"
        )

        longitude = st.number_input(
            "Longitude",
            min_value=-180.000000,
            max_value=180.000000,
            value=float(st.session_state.current_longitude),
            format="%.6f"
        )

        st.markdown("#### Casualty and Rescue Information")

        col1, col2, col3 = st.columns(3)

        with col1:
            casualties = st.number_input(
                "Casualties",
                min_value=0,
                step=1
            )

        with col2:
            injured = st.number_input(
                "Injured",
                min_value=0,
                step=1
            )

        with col3:
            trapped = st.number_input(
                "Trapped / Missing",
                min_value=0,
                step=1
            )

        st.markdown("#### Damage Information")

        col4, col5 = st.columns(2)

        with col4:
            damaged_buildings = st.number_input(
                "Damaged Buildings",
                min_value=0,
                step=1
            )

        with col5:
            road_status = st.selectbox(
                "Road Status",
                [
                    "Passable",
                    "Partially Blocked",
                    "Not Passable",
                    "Unknown"
                ]
            )

        remarks = st.text_area(
            "Remarks / Situation Description"
        )

        uploaded_photos = st.file_uploader(
            "Attach Incident Photos",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        priority_score, priority = calculate_priority(
            casualties,
            injured,
            trapped,
            damaged_buildings,
            road_status
        )

        st.markdown("#### AI-Assisted Priority Assessment")

        if priority == "High":
            st.error(f"Priority: {priority} | Score: {priority_score}")
        elif priority == "Medium":
            st.warning(f"Priority: {priority} | Score: {priority_score}")
        else:
            st.success(f"Priority: {priority} | Score: {priority_score}")

        submitted = st.form_submit_button(
            "Submit Incident Report",
            use_container_width=True
        )

    if submitted:
        validation_errors = validate_incident_report(
            barangay,
            municipality,
            latitude,
            longitude
        )

        if validation_errors:
            for error in validation_errors:
                st.error(error)

        else:
            save_report(
                barangay,
                municipality,
                latitude,
                longitude,
                casualties,
                injured,
                trapped,
                damaged_buildings,
                road_status,
                priority_score,
                priority,
                remarks,
                uploaded_photos
            )

            log_activity(
                "Incident Report Submitted",
                f"{barangay}, {municipality} | Priority: {priority}"
            )

            st.success("Incident report submitted successfully.")

            st.session_state.incident_barangay = ""
            st.session_state.incident_municipality = ""
            st.session_state.incident_full_address = ""

            reset_incident_form(st)
            st.rerun()