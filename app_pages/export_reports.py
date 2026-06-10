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


def show_export_reports():
    show_page_title(
        "Export Reports",
        "Download incident data and generated situation reports."
    )

    reports_df = load_reports()
    photos_by_report = build_photos_by_report(reports_df)

    if not reports_df.empty:
        show_section_title("Incident Report Dataset")

        csv = reports_df.to_csv(index=False).encode("utf-8")

        st.dataframe(reports_df, use_container_width=True)

        st.download_button(
            label="Download Incident Reports as CSV",
            data=csv,
            file_name="e_warps_incident_reports.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.divider()

        show_section_title("SITREP PDF Export")

        prepared_by = st.text_input("Prepared By")
        prepared_role = st.text_input(
            "Role / Designation",
            value=st.session_state.user_role
        )
        reviewed_by = st.text_input("Reviewed By")
        approved_by = st.text_input("Approved By")

        sitrep_text = generate_sitrep_text(
            reports_df,
            load_alerts()
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

        st.info(
            "Incident photos are now included in the SITREP PDF when the uploaded photo files are available."
        )

        log_activity(
            "Reports Exported",
            "CSV/PDF export page accessed"
        )

    else:
        st.warning("No reports available to export.")