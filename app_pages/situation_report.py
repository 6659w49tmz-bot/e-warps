import streamlit as st

from database import load_reports, load_alerts, log_activity
from helpers import generate_sitrep_text, generate_pdf_sitrep
from ui import show_page_title, show_section_title


def show_situation_report():
    show_page_title(
        "AI-Assisted Situation Report",
        "Generate a command-style summary based on alerts and incident reports."
    )

    reports_df = load_reports()
    alerts_df = load_alerts()

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

    pdf_buffer = generate_pdf_sitrep(
        sitrep_text,
        reports_df,
        prepared_by=prepared_by,
        prepared_role=prepared_role,
        reviewed_by=reviewed_by,
        approved_by=approved_by
    )

    st.download_button(
        label="Download SITREP as PDF",
        data=pdf_buffer,
        file_name="e_warps_sitrep.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    log_activity(
        "SITREP Generated",
        "Situation report viewed/generated"
    )