import streamlit as st

from database import load_activity_log
from ui import show_page_title, show_section_title


def show_activity_log():
    show_page_title(
        "Activity Log / Audit Trail",
        "Review recorded user actions and system activity."
    )

    logs_df = load_activity_log()

    if not logs_df.empty:
        show_section_title("System Activity")
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.warning("No activity logs recorded yet.")