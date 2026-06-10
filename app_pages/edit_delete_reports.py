import os

import pandas as pd
import streamlit as st

from database import (
    load_reports,
    load_photos,
    update_report,
    delete_report
)
from helpers import calculate_priority


def show_edit_delete_reports():
    st.title("✏️ Edit / Delete Incident Reports")

    reports_df = load_reports()

    if reports_df.empty:
        st.warning("No reports available.")

    else:
        st.dataframe(reports_df, use_container_width=True)

        selected_report_id = st.selectbox(
            "Select Report ID to Edit/Delete",
            reports_df["ID"].tolist()
        )

        selected_report = reports_df[
            reports_df["ID"] == selected_report_id
        ].iloc[0]

        with st.form("edit_report_form"):
            barangay = st.text_input(
                "Barangay",
                value=selected_report["Barangay"]
            )

            municipality = st.text_input(
                "Municipality / City",
                value=selected_report["Municipality / City"]
            )

            col1, col2 = st.columns(2)

            with col1:
                latitude = st.number_input(
                    "Latitude",
                    value=float(selected_report["Latitude"]) if pd.notna(selected_report["Latitude"]) else 0.0,
                    format="%.6f"
                )

            with col2:
                longitude = st.number_input(
                    "Longitude",
                    value=float(selected_report["Longitude"]) if pd.notna(selected_report["Longitude"]) else 0.0,
                    format="%.6f"
                )

            casualties = st.number_input(
                "Casualties",
                min_value=0,
                value=int(selected_report["Casualties"])
            )

            injured = st.number_input(
                "Injured",
                min_value=0,
                value=int(selected_report["Injured"])
            )

            trapped = st.number_input(
                "Trapped Persons",
                min_value=0,
                value=int(selected_report["Trapped Persons"])
            )

            damaged_buildings = st.number_input(
                "Damaged Buildings",
                min_value=0,
                value=int(selected_report["Damaged Buildings"])
            )

            road_status_options = [
                "Passable",
                "Partially Blocked",
                "Blocked"
            ]

            road_status = st.selectbox(
                "Road Status",
                road_status_options,
                index=road_status_options.index(selected_report["Road Status"])
            )

            remarks = st.text_area(
                "Remarks",
                value=str(selected_report["Remarks"])
            )

            update_button = st.form_submit_button("Update Report")

        if update_button:
            score, priority = calculate_priority(
                casualties,
                injured,
                trapped,
                damaged_buildings,
                road_status
            )

            update_report(
                selected_report_id,
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
                remarks
            )

            st.success("Report updated.")
            st.rerun()

        st.divider()

        st.subheader("Photos")

        photos_df = load_photos(selected_report_id)

        if not photos_df.empty:
            for _, photo in photos_df.iterrows():
                if os.path.exists(photo["filepath"]):
                    st.image(
                        photo["filepath"],
                        caption=photo["filename"],
                        use_container_width=True
                    )
        else:
            st.info("No photos uploaded for this report.")

        st.divider()

        if st.button("Delete Selected Report"):
            delete_report(selected_report_id)
            st.success("Report deleted.")
            st.rerun()