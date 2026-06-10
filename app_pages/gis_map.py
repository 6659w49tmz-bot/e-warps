import folium
import streamlit as st
from streamlit_folium import st_folium

from database import load_reports
from helpers import get_marker_color, reset_incident_form
from ui import show_page_title, show_section_title, show_status_legend


def show_gis_map():
    show_page_title(
        "GIS Situational Awareness Map",
        "View affected areas based on submitted coordinates and rescue priority."
    )

    show_status_legend()

    st.divider()

    reports_df = load_reports()

    if reports_df.empty:
        st.warning("No incident reports available for mapping.")

        if st.button("Add Incident Report"):
            reset_incident_form(st)
            st.rerun()

    else:
        map_df = reports_df.copy()

        map_df = map_df[
            (map_df["Latitude"].notna()) &
            (map_df["Longitude"].notna()) &
            (map_df["Latitude"] != 0) &
            (map_df["Longitude"] != 0)
        ]

        if map_df.empty:
            st.warning("Reports exist, but no valid coordinates were entered yet.")
            st.info(
                "Use current location, search by barangay/city, or manually enter coordinates in the Incident Reports page."
            )

        else:
            center_lat = map_df["Latitude"].mean()
            center_lon = map_df["Longitude"].mean()

            incident_map = folium.Map(
                location=[
                    center_lat,
                    center_lon
                ],
                zoom_start=10
            )

            for _, report in map_df.iterrows():
                popup_text = f"""
                <b>Barangay:</b> {report["Barangay"]}<br>
                <b>Municipality/City:</b> {report["Municipality / City"]}<br>
                <b>Priority:</b> {report["Priority"]}<br>
                <b>Score:</b> {report["Priority Score"]}<br>
                <b>Casualties:</b> {report["Casualties"]}<br>
                <b>Injured:</b> {report["Injured"]}<br>
                <b>Trapped:</b> {report["Trapped Persons"]}<br>
                <b>Damaged Buildings:</b> {report["Damaged Buildings"]}<br>
                <b>Road Status:</b> {report["Road Status"]}
                """

                folium.Marker(
                    location=[
                        report["Latitude"],
                        report["Longitude"]
                    ],
                    popup=folium.Popup(
                        popup_text,
                        max_width=350
                    ),
                    tooltip=f"{report['Barangay']} - {report['Priority']}",
                    icon=folium.Icon(
                        color=get_marker_color(report["Priority"]),
                        icon="info-sign"
                    )
                ).add_to(incident_map)

            st_folium(
                incident_map,
                width=None,
                height=600
            )

            st.divider()

            show_section_title("Mapped Incident Reports")
            st.dataframe(map_df, use_container_width=True)