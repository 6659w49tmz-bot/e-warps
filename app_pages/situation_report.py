import os

import streamlit as st

from database import load_reports, load_alerts, load_photos, log_activity
from helpers import generate_sitrep_text, generate_pdf_sitrep
from ui import show_page_title, show_section_title


def build_photos_by_report(reports_df):
    photos_by_report = {}

    if reports_df.empty:
        return photos_by_report

    for _, report in reports_df.iterrows():
        report_id = int(report["ID"])
        photos_df = load_photos(report_id)

        photos = []

        if not photos_df.empty:
            for _, photo in photos_df.iterrows():
                photos.append(
                    {
                        "filename": photo["filename"],
                        "filepath": photo["filepath"]
                    }
                )

        photos_by_report[report_id] = photos

    return photos_by_report


def show_situation_report():
    show_page_title(
        "AI-Assisted Situation Report",
        "Generate a command-style summary based on alerts, incident reports, and attached photos."
    )

    reports_df = load_reports()
    alerts_df = load_alerts()
    photos_by_report = build_photos_by_report(reports_df)

    show_section_title("PDF Report Details")

    col1, col2 = st.columns(2)

    with col1:
        prepared_by = st.text_input("Prepared By")
        prepared_role = st.text_input(
            "Role / Designation",
            value=st.session_state.user_role
        )

    with col2:
        reviewed_by = st.text_input("Reviewed By")
        approved_by = st.text_input("Approved By")

    sitrep_text = generate_sitrep_text(
        reports_df,
        alerts_df
    )

    st.divider()

    show_section_title("Generated SITREP")

    st.text_area(
        "Situation Report Text",
        value=sitrep_text,
        height=500
    )

    st.divider()

    show_section_title("Incident Photos Included in SITREP")

    if reports_df.empty:
        st.info("No incident reports available.")
    else:
        total_photo_count = 0

        sorted_reports_df = reports_df.sort_values(
            by="Priority Score",
            ascending=False
        )

        for _, report in sorted_reports_df.iterrows():
            report_id = int(report["ID"])
            report_photos = photos_by_report.get(report_id, [])

            with st.expander(
                f"{report['Barangay']}, {report['Municipality / City']} - {report['Priority']}"
            ):
                st.write(f"**Priority Score:** {report['Priority Score']}")
                st.write(f"**Remarks:** {report['Remarks']}")

                if report_photos:
                    total_photo_count += len(report_photos)

                    photo_cols = st.columns(2)

                    for index, photo in enumerate(report_photos):
                        photo_path = photo["filepath"]

                        with photo_cols[index % 2]:
                            if os.path.exists(photo_path):
                                st.image(
                                    photo_path,
                                    caption=photo["filename"],
                                    use_container_width=True
                                )
                            else:
                                st.warning(
                                    f"Photo file missing: {photo['filename']}"
                                )
                else:
                    st.info("No photos attached for this incident.")

        st.caption(
            f"Total photos attached to this SITREP: {total_photo_count}"
        )

    pdf_buffer = generate_pdf_sitrep(
        sitrep_text,
        reports_df,
        photos_by_report=photos_by_report,
        prepared_by=prepared_by,
        prepared_role=prepared_role,
        reviewed_by=reviewed_by,
        approved_by=approved_by
    )

    st.download_button(
        label="Download SITREP as PDF with Photos",
        data=pdf_buffer,
        file_name="e_warps_sitrep_with_photos.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    log_activity(
        "SITREP Generated",
        "Situation report with photos viewed/generated"
    )