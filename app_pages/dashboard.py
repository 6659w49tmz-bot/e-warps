import pandas as pd
import streamlit as st

from config import ROLE_PAGES
from database import load_reports, load_alerts
from helpers import go_to_page, reset_alert_form, reset_incident_form
from ui import show_page_title, show_status_legend, show_section_title


def show_dashboard():
    show_page_title(
        "Dashboard",
        f"Current Role: {st.session_state.user_role}"
    )

    reports_df = load_reports()
    alerts_df = load_alerts()

    total_reports = len(reports_df)
    affected_areas = reports_df["Barangay"].nunique() if not reports_df.empty else 0
    critical_areas = len(reports_df[reports_df["Priority"] == "🔴 CRITICAL"]) if not reports_df.empty else 0
    total_alerts = len(alerts_df)

    allowed_pages = ROLE_PAGES.get(
        st.session_state.user_role,
        ROLE_PAGES["Admin"]
    )

    show_section_title("Operational Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Earthquake Alerts",
            value=total_alerts
        )

    with col2:
        st.metric(
            label="Incident Reports",
            value=total_reports
        )

    with col3:
        st.metric(
            label="Affected Areas",
            value=affected_areas
        )

    with col4:
        st.metric(
            label="Critical Areas",
            value=critical_areas
        )

    st.divider()

    show_section_title("Incident Charts")

    if not reports_df.empty:
        priority_counts = reports_df["Priority"].value_counts().reset_index()
        priority_counts.columns = ["Priority", "Count"]

        impact_totals = pd.DataFrame(
            {
                "Category": [
                    "Casualties",
                    "Injured",
                    "Trapped Persons",
                    "Damaged Buildings"
                ],
                "Total": [
                    int(reports_df["Casualties"].sum()),
                    int(reports_df["Injured"].sum()),
                    int(reports_df["Trapped Persons"].sum()),
                    int(reports_df["Damaged Buildings"].sum())
                ]
            }
        )

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.write("**Priority Classification Count**")
            st.bar_chart(
                priority_counts,
                x="Priority",
                y="Count"
            )

        with chart_col2:
            st.write("**Reported Impact Summary**")
            st.bar_chart(
                impact_totals,
                x="Category",
                y="Total"
            )

    else:
        st.info("Charts will appear once incident reports are submitted.")

    st.divider()

    show_status_legend()

    st.divider()

    show_section_title("Quick Actions")

    quick_actions = []

    if "Earthquake Alerts" in allowed_pages:
        quick_actions.append(
            {
                "label": "➕ Add Alert",
                "page": "Earthquake Alerts",
                "type": "alert"
            }
        )

    if "Incident Reports" in allowed_pages:
        quick_actions.append(
            {
                "label": "📝 Add Report",
                "page": "Incident Reports",
                "type": "report"
            }
        )

    if "Prioritization" in allowed_pages:
        quick_actions.append(
            {
                "label": "🚨 Prioritization",
                "page": "Prioritization",
                "type": "page"
            }
        )

    if "Situation Report" in allowed_pages:
        quick_actions.append(
            {
                "label": "📄 SITREP",
                "page": "Situation Report",
                "type": "page"
            }
        )

    if quick_actions:
        action_cols = st.columns(len(quick_actions))

        for index, action in enumerate(quick_actions):
            with action_cols[index]:
                if st.button(action["label"], use_container_width=True):
                    if action["type"] == "alert":
                        reset_alert_form(st)

                    elif action["type"] == "report":
                        reset_incident_form(st)

                    else:
                        go_to_page(st, action["page"])

                    st.rerun()
    else:
        st.info("No quick actions available for this role.")

    st.divider()

    show_section_title("Latest Earthquake Alert")

    if not alerts_df.empty:
        latest_alert = alerts_df.iloc[0]

        st.success(
            f"""
            **Magnitude:** {latest_alert["Magnitude"]}  
            **Epicenter:** {latest_alert["Epicenter"]}  
            **Depth:** {latest_alert["Depth"]} km  
            **Date/Time:** {latest_alert["Date/Time"]}  
            **Remarks:** {latest_alert["Remarks"]}
            """
        )

    else:
        st.info("No earthquake alerts recorded.")

    st.divider()

    show_section_title("Latest Incident Reports")

    if not reports_df.empty:
        st.dataframe(
            reports_df,
            use_container_width=True
        )

    else:
        st.warning("No incident reports submitted yet.")