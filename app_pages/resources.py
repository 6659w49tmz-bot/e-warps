import streamlit as st

from database import (
    save_resource,
    load_resources,
    update_resource,
    delete_resource,
    load_reports
)
from helpers import generate_resource_recommendation
from ui import show_page_title, show_section_title


def show_resources():
    show_page_title(
        "Resource Allocation Module",
        "Encode available response assets and generate suggested deployment priorities."
    )

    reports_df = load_reports()
    resources_df = load_resources()

    show_section_title("Available Resources")

    if not resources_df.empty:
        st.dataframe(resources_df, use_container_width=True)
    else:
        st.warning("No resources encoded yet.")

    st.divider()

    show_section_title("Add Resource")

    with st.form("resource_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            resource_name = st.text_input(
                "Resource Name",
                placeholder="Example: QRF Team, Ambulance, Rescue Vehicle"
            )

        with col2:
            quantity = st.number_input(
                "Available Quantity",
                min_value=0,
                value=0
            )

        resource_remarks = st.text_area("Remarks")

        submit_resource = st.form_submit_button("Save Resource")

    if submit_resource:
        save_resource(
            resource_name,
            quantity,
            resource_remarks
        )

        st.success("Resource saved.")
        st.rerun()

    st.divider()

    show_section_title("Suggested Allocation")

    allocation_text = generate_resource_recommendation(
        reports_df,
        resources_df
    )

    st.text_area(
        "AI-Assisted Resource Allocation Recommendation",
        value=allocation_text,
        height=400
    )

    st.divider()

    show_section_title("Edit / Delete Resource")

    if not resources_df.empty:
        selected_resource_id = st.selectbox(
            "Select Resource ID",
            resources_df["ID"].tolist()
        )

        selected_resource = resources_df[
            resources_df["ID"] == selected_resource_id
        ].iloc[0]

        with st.form("edit_resource_form"):
            edited_resource_name = st.text_input(
                "Resource Name",
                value=selected_resource["Resource"]
            )

            edited_quantity = st.number_input(
                "Quantity",
                min_value=0,
                value=int(selected_resource["Quantity"])
            )

            edited_remarks = st.text_area(
                "Remarks",
                value=str(selected_resource["Remarks"])
            )

            update_resource_button = st.form_submit_button("Update Resource")

        if update_resource_button:
            update_resource(
                selected_resource_id,
                edited_resource_name,
                edited_quantity,
                edited_remarks
            )

            st.success("Resource updated.")
            st.rerun()

        if st.button("Delete Selected Resource"):
            delete_resource(selected_resource_id)
            st.success("Resource deleted.")
            st.rerun()