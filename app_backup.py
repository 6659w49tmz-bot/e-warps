import streamlit as st
import pandas as pd
import sqlite3
import os
import uuid
import folium
from datetime import datetime
from io import BytesIO

from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="E-WARPS",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================
# FILE / DATABASE SETUP
# =========================
DB_FILE = "ewarps.db"
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def get_connection():
    return sqlite3.connect(DB_FILE)


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    for column in columns:
        if column[1] == column_name:
            return True

    return False


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            magnitude REAL,
            epicenter TEXT,
            depth INTEGER,
            alert_time TEXT,
            remarks TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_time TEXT,
            barangay TEXT,
            municipality TEXT,
            latitude REAL,
            longitude REAL,
            casualties INTEGER,
            injured INTEGER,
            trapped INTEGER,
            damaged_buildings INTEGER,
            road_status TEXT,
            priority_score INTEGER,
            priority TEXT,
            remarks TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            filename TEXT,
            filepath TEXT,
            FOREIGN KEY(report_id) REFERENCES reports(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_name TEXT,
            available_quantity INTEGER,
            remarks TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_time TEXT,
            user_role TEXT,
            action TEXT,
            details TEXT
        )
        """
    )

    if not column_exists(cursor, "reports", "latitude"):
        cursor.execute("ALTER TABLE reports ADD COLUMN latitude REAL")

    if not column_exists(cursor, "reports", "longitude"):
        cursor.execute("ALTER TABLE reports ADD COLUMN longitude REAL")

    conn.commit()
    conn.close()


initialize_database()


# =========================
# SESSION STATE
# =========================
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Dashboard"

if "incident_form_counter" not in st.session_state:
    st.session_state.incident_form_counter = 0

if "alert_form_counter" not in st.session_state:
    st.session_state.alert_form_counter = 0

if "current_latitude" not in st.session_state:
    st.session_state.current_latitude = 0.000000

if "current_longitude" not in st.session_state:
    st.session_state.current_longitude = 0.000000

if "user_role" not in st.session_state:
    st.session_state.user_role = "Commander"


# =========================
# UTILITY FUNCTIONS
# =========================
def log_activity(action, details=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO activity_log (
            log_time,
            user_role,
            action,
            details
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.user_role,
            action,
            details
        )
    )

    conn.commit()
    conn.close()


def calculate_priority(casualties, injured, trapped, damaged_buildings, road_status):
    score = 0
    score += casualties * 10
    score += injured * 3
    score += trapped * 15
    score += damaged_buildings

    if road_status == "Partially Blocked":
        score += 20
    elif road_status == "Blocked":
        score += 40

    if score >= 100:
        return score, "🔴 CRITICAL"
    elif score >= 60:
        return score, "🟠 SEVERE"
    elif score >= 30:
        return score, "🟡 MODERATE"
    else:
        return score, "🟢 LOW"


def get_marker_color(priority):
    if priority == "🔴 CRITICAL":
        return "red"
    elif priority == "🟠 SEVERE":
        return "orange"
    elif priority == "🟡 MODERATE":
        return "lightred"
    else:
        return "green"


def generate_recommendations(priority):
    if priority == "🔴 CRITICAL":
        return [
            "Activate Incident Command Post (ICP)",
            "Deploy Quick Reaction Force (QRF)",
            "Deploy Search and Rescue Team",
            "Deploy Medical Team",
            "Request Engineering Assessment Team",
            "Coordinate with LGU/MDRRMO and Barangay Officials",
            "Prepare evacuation area and casualty collection point"
        ]

    elif priority == "🟠 SEVERE":
        return [
            "Deploy assessment team immediately",
            "Place QRF on high alert",
            "Prepare medical support",
            "Coordinate with MDRRMO",
            "Monitor road access and lifeline utilities"
        ]

    elif priority == "🟡 MODERATE":
        return [
            "Conduct rapid damage assessment",
            "Place response team on standby",
            "Monitor incoming reports",
            "Coordinate with barangay officials"
        ]

    else:
        return [
            "Continue monitoring",
            "Validate field report",
            "Await additional updates"
        ]


def show_recommendations(priority):
    for action in generate_recommendations(priority):
        st.write(f"✅ {action}")


def go_to_page(page_name):
    st.session_state.selected_page = page_name


def reset_alert_form():
    st.session_state.alert_form_counter += 1
    st.session_state.selected_page = "Earthquake Alerts"


def reset_incident_form():
    st.session_state.incident_form_counter += 1
    st.session_state.current_latitude = 0.000000
    st.session_state.current_longitude = 0.000000
    st.session_state.selected_page = "Incident Reports"


def geocode_location(barangay, municipality):
    geolocator = Nominatim(user_agent="e-warps-capstone")
    search_query = f"{barangay}, {municipality}, Philippines"

    try:
        location = geolocator.geocode(search_query, timeout=10)

        if location:
            return float(location.latitude), float(location.longitude), location.address

        return None, None, None

    except (GeocoderTimedOut, GeocoderServiceError):
        return None, None, None


# =========================
# DATABASE FUNCTIONS
# =========================
def save_alert(magnitude, epicenter, depth, alert_time, remarks):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO alerts (
            magnitude,
            epicenter,
            depth,
            alert_time,
            remarks
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            magnitude,
            epicenter,
            depth,
            alert_time,
            remarks
        )
    )

    conn.commit()
    conn.close()

    log_activity("Earthquake Alert Saved", f"Magnitude {magnitude}, Epicenter {epicenter}")


def load_alerts():
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            id AS ID,
            magnitude AS Magnitude,
            epicenter AS Epicenter,
            depth AS Depth,
            alert_time AS "Date/Time",
            remarks AS Remarks
        FROM alerts
        ORDER BY id DESC
        """,
        conn
    )

    conn.close()
    return df


def save_report(
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
):
    conn = get_connection()
    cursor = conn.cursor()

    report_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute(
        """
        INSERT INTO reports (
            report_time,
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
            remarks
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_time,
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
            remarks
        )
    )

    report_id = cursor.lastrowid

    if uploaded_photos:
        for photo in uploaded_photos:
            file_extension = os.path.splitext(photo.name)[1]
            safe_filename = f"{uuid.uuid4()}{file_extension}"
            filepath = os.path.join(UPLOAD_FOLDER, safe_filename)

            with open(filepath, "wb") as file:
                file.write(photo.getbuffer())

            cursor.execute(
                """
                INSERT INTO photos (
                    report_id,
                    filename,
                    filepath
                )
                VALUES (?, ?, ?)
                """,
                (
                    report_id,
                    photo.name,
                    filepath
                )
            )

    conn.commit()
    conn.close()

    log_activity("Incident Report Saved", f"{barangay}, {municipality}, Priority: {priority}")

    return report_id


def update_report(
    report_id,
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
    remarks
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE reports
        SET
            barangay = ?,
            municipality = ?,
            latitude = ?,
            longitude = ?,
            casualties = ?,
            injured = ?,
            trapped = ?,
            damaged_buildings = ?,
            road_status = ?,
            priority_score = ?,
            priority = ?,
            remarks = ?
        WHERE id = ?
        """,
        (
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
            report_id
        )
    )

    conn.commit()
    conn.close()

    log_activity("Incident Report Updated", f"Report ID {report_id}, {barangay}, Priority: {priority}")


def delete_report(report_id):
    photos_df = load_photos(report_id)

    for _, photo in photos_df.iterrows():
        filepath = photo["filepath"]

        if os.path.exists(filepath):
            os.remove(filepath)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM photos WHERE report_id = ?", (report_id,))
    cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))

    conn.commit()
    conn.close()

    log_activity("Incident Report Deleted", f"Report ID {report_id}")


def load_reports():
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            reports.id AS ID,
            reports.report_time AS "Date/Time",
            reports.barangay AS Barangay,
            reports.municipality AS "Municipality / City",
            reports.latitude AS Latitude,
            reports.longitude AS Longitude,
            reports.casualties AS Casualties,
            reports.injured AS Injured,
            reports.trapped AS "Trapped Persons",
            reports.damaged_buildings AS "Damaged Buildings",
            reports.road_status AS "Road Status",
            reports.priority_score AS "Priority Score",
            reports.priority AS Priority,
            reports.remarks AS Remarks,
            COUNT(photos.id) AS "Photo Count"
        FROM reports
        LEFT JOIN photos ON reports.id = photos.report_id
        GROUP BY reports.id
        ORDER BY reports.priority_score DESC
        """,
        conn
    )

    conn.close()
    return df


def load_photos(report_id):
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            filename,
            filepath
        FROM photos
        WHERE report_id = ?
        """,
        conn,
        params=(report_id,)
    )

    conn.close()
    return df


def save_resource(resource_name, available_quantity, remarks):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO resources (
            resource_name,
            available_quantity,
            remarks
        )
        VALUES (?, ?, ?)
        """,
        (
            resource_name,
            available_quantity,
            remarks
        )
    )

    conn.commit()
    conn.close()

    log_activity("Resource Added", f"{resource_name}: {available_quantity}")


def load_resources():
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            id AS ID,
            resource_name AS Resource,
            available_quantity AS Quantity,
            remarks AS Remarks
        FROM resources
        ORDER BY resource_name ASC
        """,
        conn
    )

    conn.close()
    return df


def update_resource(resource_id, resource_name, available_quantity, remarks):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE resources
        SET
            resource_name = ?,
            available_quantity = ?,
            remarks = ?
        WHERE id = ?
        """,
        (
            resource_name,
            available_quantity,
            remarks,
            resource_id
        )
    )

    conn.commit()
    conn.close()

    log_activity("Resource Updated", f"{resource_name}: {available_quantity}")


def delete_resource(resource_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM resources WHERE id = ?", (resource_id,))

    conn.commit()
    conn.close()

    log_activity("Resource Deleted", f"Resource ID {resource_id}")


def load_activity_log():
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            id AS ID,
            log_time AS "Date/Time",
            user_role AS "User Role",
            action AS Action,
            details AS Details
        FROM activity_log
        ORDER BY id DESC
        """,
        conn
    )

    conn.close()
    return df


def clear_reports():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM photos")
    cursor.execute("DELETE FROM reports")

    conn.commit()
    conn.close()

    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        if os.path.isfile(filepath):
            os.remove(filepath)

    log_activity("All Incident Reports Cleared", "All reports and uploaded photos removed")


def clear_alerts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM alerts")

    conn.commit()
    conn.close()

    log_activity("All Earthquake Alerts Cleared", "All alerts removed")


def clear_resources():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM resources")

    conn.commit()
    conn.close()

    log_activity("All Resources Cleared", "All resources removed")


def clear_activity_log():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM activity_log")

    conn.commit()
    conn.close()


# =========================
# SITREP FUNCTIONS
# =========================
def generate_sitrep_text(reports_df, alerts_df):
    now_text = datetime.now().strftime("%d %B %Y %H%MH")

    if reports_df.empty:
        return f"As of {now_text}, no incident reports have been recorded in E-WARPS."

    total_reports = len(reports_df)
    affected_areas = reports_df["Barangay"].nunique()
    total_casualties = int(reports_df["Casualties"].sum())
    total_injured = int(reports_df["Injured"].sum())
    total_trapped = int(reports_df["Trapped Persons"].sum())
    total_damaged = int(reports_df["Damaged Buildings"].sum())

    critical_count = len(reports_df[reports_df["Priority"] == "🔴 CRITICAL"])
    severe_count = len(reports_df[reports_df["Priority"] == "🟠 SEVERE"])
    moderate_count = len(reports_df[reports_df["Priority"] == "🟡 MODERATE"])
    low_count = len(reports_df[reports_df["Priority"] == "🟢 LOW"])

    sorted_df = reports_df.sort_values(by="Priority Score", ascending=False)
    top = sorted_df.iloc[0]

    if not alerts_df.empty:
        latest_alert = alerts_df.iloc[0]
        alert_text = (
            f"The latest recorded earthquake alert indicates a magnitude "
            f"{latest_alert['Magnitude']} earthquake with epicenter at "
            f"{latest_alert['Epicenter']} and depth of {latest_alert['Depth']} km."
        )
    else:
        alert_text = "No earthquake alert has been recorded in the system."

    sitrep = f"""
SITUATION REPORT

As of {now_text}, E-WARPS recorded {total_reports} incident report/s affecting {affected_areas} barangay/area/s.

{alert_text}

Current reported impact:
- Total casualties: {total_casualties}
- Total injured persons: {total_injured}
- Total trapped persons: {total_trapped}
- Total damaged buildings/structures: {total_damaged}

Priority classification:
- Critical areas: {critical_count}
- Severe areas: {severe_count}
- Moderate areas: {moderate_count}
- Low priority areas: {low_count}

The highest priority area is {top['Barangay']}, {top['Municipality / City']}, classified as {top['Priority']} with a priority score of {top['Priority Score']}.

Recommended command action:
Immediate attention should be given to the highest priority areas. For critical areas, the commander may consider activation of the Incident Command Post, deployment of QRF, SAR, medical teams, and engineering assessment teams, and coordination with LGU/MDRRMO and barangay officials.

This report is AI-assisted and intended to support command decision-making. Final approval and action remain under human command authority.
"""

    return sitrep.strip()


def generate_pdf_sitrep(sitrep_text, reports_df):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("E-WARPS Situation Report", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    for line in sitrep_text.split("\n"):
        if line.strip() == "":
            elements.append(Spacer(1, 8))
        else:
            elements.append(Paragraph(line, styles["BodyText"]))

    elements.append(Spacer(1, 16))

    if not reports_df.empty:
        elements.append(Paragraph("Incident Report Summary", styles["Heading2"]))

        table_data = [
            [
                "Barangay",
                "City",
                "Casualties",
                "Injured",
                "Trapped",
                "Score",
                "Priority"
            ]
        ]

        for _, row in reports_df.iterrows():
            table_data.append(
                [
                    str(row["Barangay"]),
                    str(row["Municipality / City"]),
                    str(row["Casualties"]),
                    str(row["Injured"]),
                    str(row["Trapped Persons"]),
                    str(row["Priority Score"]),
                    str(row["Priority"])
                ]
            )

        table = Table(table_data, repeatRows=1)

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        elements.append(table)

    doc.build(elements)

    buffer.seek(0)
    return buffer


def generate_resource_recommendation(reports_df, resources_df):
    if reports_df.empty:
        return "No incident reports available for resource allocation."

    if resources_df.empty:
        return "No resources have been encoded. Add available QRF, medical, SAR, engineering, vehicles, and equipment first."

    sorted_reports = reports_df.sort_values(by="Priority Score", ascending=False)

    output = []

    output.append("Suggested Resource Allocation:")
    output.append("")

    for _, report in sorted_reports.iterrows():
        output.append(f"{report['Barangay']} - {report['Priority']}")

        if report["Priority"] == "🔴 CRITICAL":
            output.append("- Prioritize deployment of QRF, SAR, medical team, engineering assessment team, and available transport.")
        elif report["Priority"] == "🟠 SEVERE":
            output.append("- Deploy assessment team, prepare QRF, and coordinate medical support.")
        elif report["Priority"] == "🟡 MODERATE":
            output.append("- Deploy assessment team if available and monitor situation.")
        else:
            output.append("- Monitor and validate incoming reports.")

        output.append("")

    output.append("Available Resources:")
    for _, resource in resources_df.iterrows():
        output.append(f"- {resource['Resource']}: {resource['Quantity']} available")

    return "\n".join(output)


# =========================
# SIDEBAR
# =========================
role_options = [
    "Commander",
    "Operations Officer",
    "Responder",
    "Admin"
]

st.sidebar.title("🌏 E-WARPS")

st.session_state.user_role = st.sidebar.selectbox(
    "User Role",
    role_options,
    index=role_options.index(st.session_state.user_role)
)

all_pages = [
    "Dashboard",
    "Earthquake Alerts",
    "Incident Reports",
    "Prioritization",
    "GIS Map",
    "Command Recommendations",
    "Situation Report",
    "Resources",
    "Edit/Delete Reports",
    "Export Reports",
    "Activity Log",
    "Settings"
]

role_pages = {
    "Commander": [
        "Dashboard",
        "Prioritization",
        "GIS Map",
        "Command Recommendations",
        "Situation Report",
        "Resources",
        "Export Reports",
        "Activity Log"
    ],
    "Operations Officer": [
        "Dashboard",
        "Earthquake Alerts",
        "Incident Reports",
        "Prioritization",
        "GIS Map",
        "Command Recommendations",
        "Situation Report",
        "Resources",
        "Edit/Delete Reports",
        "Export Reports",
        "Activity Log"
    ],
    "Responder": [
        "Dashboard",
        "Incident Reports",
        "GIS Map"
    ],
    "Admin": all_pages
}

pages = role_pages.get(st.session_state.user_role, all_pages)

if st.session_state.selected_page not in pages:
    st.session_state.selected_page = pages[0]

page = st.sidebar.radio(
    "Navigation",
    pages,
    index=pages.index(st.session_state.selected_page)
)

st.session_state.selected_page = page


# =========================
# DASHBOARD
# =========================
if page == "Dashboard":
    st.title("🌏 E-WARPS Dashboard")

    st.caption(f"Current Role: {st.session_state.user_role}")

    st.subheader(
        "AI-Assisted Earthquake Alert Integration, Damage Assessment, Rescue Prioritization, and Command Decision Support System"
    )

    reports_df = load_reports()
    alerts_df = load_alerts()

    total_reports = len(reports_df)
    affected_areas = reports_df["Barangay"].nunique() if not reports_df.empty else 0
    critical_areas = len(reports_df[reports_df["Priority"] == "🔴 CRITICAL"]) if not reports_df.empty else 0
    total_alerts = len(alerts_df)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Earthquake Alerts", total_alerts)
    col2.metric("Incident Reports", total_reports)
    col3.metric("Affected Areas", affected_areas)
    col4.metric("Critical Areas", critical_areas)

    st.divider()

    st.subheader("Quick Actions")

    quick_cols = st.columns(4)

    with quick_cols[0]:
        if st.button("➕ Add Alert", use_container_width=True):
            reset_alert_form()
            st.rerun()

    with quick_cols[1]:
        if st.button("📝 Add Report", use_container_width=True):
            reset_incident_form()
            st.rerun()

    with quick_cols[2]:
        if st.button("🚨 Prioritization", use_container_width=True):
            go_to_page("Prioritization")
            st.rerun()

    with quick_cols[3]:
        if st.button("📄 SITREP", use_container_width=True):
            go_to_page("Situation Report")
            st.rerun()

    st.divider()

    st.header("Latest Earthquake Alert")

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

    st.header("Latest Incident Reports")

    if not reports_df.empty:
        st.dataframe(reports_df, use_container_width=True)
    else:
        st.warning("No incident reports submitted yet.")


# =========================
# EARTHQUAKE ALERTS
# =========================
elif page == "Earthquake Alerts":
    st.title("📡 Earthquake Alerts")

    alert_form_key = f"alert_form_{st.session_state.alert_form_counter}"

    with st.form(alert_form_key, clear_on_submit=True):
        magnitude = st.number_input("Magnitude", min_value=0.0, value=0.0, step=0.1)
        epicenter = st.text_input("Epicenter")
        depth = st.number_input("Depth in km", min_value=0, value=0)
        alert_time = st.text_input("Date/Time", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        alert_remarks = st.text_area("Remarks")

        submit_alert = st.form_submit_button("Save Earthquake Alert")

    col_clear_alert, col_dashboard_alert = st.columns(2)

    with col_clear_alert:
        if st.button("🧹 Clear Alert Input Fields", use_container_width=True):
            reset_alert_form()
            st.rerun()

    with col_dashboard_alert:
        if st.button("Go Back to Dashboard", use_container_width=True):
            go_to_page("Dashboard")
            st.rerun()

    if submit_alert:
        save_alert(magnitude, epicenter, depth, alert_time, alert_remarks)
        st.success("Earthquake alert saved permanently.")

    alerts_df = load_alerts()

    if not alerts_df.empty:
        st.divider()
        st.subheader("Saved Earthquake Alerts")
        st.dataframe(alerts_df, use_container_width=True)


# =========================
# INCIDENT REPORTS
# =========================
elif page == "Incident Reports":
    st.title("📝 Incident Reports")

    st.subheader("📍 Location Capture")

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
        st.info("Click the geolocation button below and allow location permission when the browser asks.")

        location = streamlit_geolocation()

        if location:
            latitude_result = location.get("latitude")
            longitude_result = location.get("longitude")

            if latitude_result is not None and longitude_result is not None:
                st.session_state.current_latitude = float(latitude_result)
                st.session_state.current_longitude = float(longitude_result)

                st.success(
                    f"Current device location captured: {st.session_state.current_latitude:.6f}, {st.session_state.current_longitude:.6f}"
                )

    elif location_method == "Search by Barangay / City":
        st.info("Type the barangay and city/municipality, then click Find Coordinates.")

        search_col1, search_col2 = st.columns(2)

        with search_col1:
            search_barangay = st.text_input("Barangay / Location Name for Search")

        with search_col2:
            search_municipality = st.text_input("Municipality / City for Search")

        if st.button("📍 Find Coordinates from Location Name", use_container_width=True):
            lat, lon, address = geocode_location(search_barangay, search_municipality)

            if lat is not None and lon is not None:
                st.session_state.current_latitude = lat
                st.session_state.current_longitude = lon

                st.success(f"Coordinates found: {lat:.6f}, {lon:.6f}")
                st.write(f"**Matched Address:** {address}")
            else:
                st.error("No coordinates found. Try adding province/region or use manual coordinates.")

    else:
        st.info("Enter the coordinates manually in the form below.")

    form_key = f"incident_form_{st.session_state.incident_form_counter}"

    with st.form(form_key, clear_on_submit=True):
        barangay = st.text_input("Barangay")
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

        casualties = st.number_input("Number of Casualties", min_value=0, value=0)
        injured = st.number_input("Number of Injured Persons", min_value=0, value=0)
        trapped = st.number_input("Number of Trapped Persons", min_value=0, value=0)
        damaged_buildings = st.number_input("Damaged Buildings", min_value=0, value=0)

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

    col_clear_report, col_dashboard_report = st.columns(2)

    with col_clear_report:
        if st.button("🧹 Clear Report Input Fields", use_container_width=True):
            reset_incident_form()
            st.rerun()

    with col_dashboard_report:
        if st.button("Go Back to Dashboard", use_container_width=True):
            go_to_page("Dashboard")
            st.rerun()

    if submit_report:
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

        submitted_df = load_reports()
        submitted_df = submitted_df[submitted_df["ID"] == report_id]

        st.subheader("Submitted Report")
        st.dataframe(submitted_df, use_container_width=True)

        photos_df = load_photos(report_id)

        if not photos_df.empty:
            st.subheader("Uploaded Photos")

            for _, photo in photos_df.iterrows():
                if os.path.exists(photo["filepath"]):
                    st.image(photo["filepath"], caption=photo["filename"], use_container_width=True)

        st.subheader("🧠 AI-Assisted Command Recommendations")
        show_recommendations(priority)

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("➕ Submit Another Incident Report", use_container_width=True):
                reset_incident_form()
                st.rerun()

        with col2:
            if st.button("🚨 View Prioritization", use_container_width=True):
                go_to_page("Prioritization")
                st.rerun()

        with col3:
            if st.button("🗺️ View GIS Map", use_container_width=True):
                go_to_page("GIS Map")
                st.rerun()


# =========================
# PRIORITIZATION
# =========================
elif page == "Prioritization":
    st.title("🚨 Rescue Prioritization")

    reports_df = load_reports()

    if not reports_df.empty:
        reports_df = reports_df.sort_values(by="Priority Score", ascending=False)
        st.dataframe(reports_df, use_container_width=True)

        top = reports_df.iloc[0]

        st.subheader("Top Priority Area")
        st.error(f"{top['Barangay']} - {top['Priority']}")
        st.metric("Priority Score", int(top["Priority Score"]))

    else:
        st.warning("No reports available for prioritization.")


# =========================
# GIS MAP
# =========================
elif page == "GIS Map":
    st.title("🗺️ GIS Situational Awareness Map")

    reports_df = load_reports()

    if reports_df.empty:
        st.warning("No incident reports available for mapping.")

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

        else:
            center_lat = map_df["Latitude"].mean()
            center_lon = map_df["Longitude"].mean()

            incident_map = folium.Map(
                location=[center_lat, center_lon],
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
                    location=[report["Latitude"], report["Longitude"]],
                    popup=folium.Popup(popup_text, max_width=350),
                    tooltip=f"{report['Barangay']} - {report['Priority']}",
                    icon=folium.Icon(
                        color=get_marker_color(report["Priority"]),
                        icon="info-sign"
                    )
                ).add_to(incident_map)

            st_folium(incident_map, width=None, height=600)

            st.subheader("Mapped Incident Reports")
            st.dataframe(map_df, use_container_width=True)


# =========================
# COMMAND RECOMMENDATIONS
# =========================
elif page == "Command Recommendations":
    st.title("🧠 Command Recommendations")

    reports_df = load_reports()

    if not reports_df.empty:
        reports_df = reports_df.sort_values(by="Priority Score", ascending=False)

        for _, report in reports_df.iterrows():
            st.subheader(f"{report['Barangay']} - {report['Priority']}")
            st.write(f"**Municipality / City:** {report['Municipality / City']}")
            st.write(f"**Priority Score:** {report['Priority Score']}")
            st.write(f"**Road Status:** {report['Road Status']}")
            st.write(f"**Latitude:** {report['Latitude']}")
            st.write(f"**Longitude:** {report['Longitude']}")
            st.write(f"**Remarks:** {report['Remarks']}")

            show_recommendations(report["Priority"])

            photos_df = load_photos(report["ID"])

            if not photos_df.empty:
                with st.expander("View Incident Photos"):
                    for _, photo in photos_df.iterrows():
                        if os.path.exists(photo["filepath"]):
                            st.image(photo["filepath"], caption=photo["filename"], use_container_width=True)

            st.divider()

    else:
        st.warning("No reports available for command recommendations.")


# =========================
# SITUATION REPORT
# =========================
elif page == "Situation Report":
    st.title("📄 AI-Assisted Situation Report")

    reports_df = load_reports()
    alerts_df = load_alerts()

    sitrep_text = generate_sitrep_text(reports_df, alerts_df)

    st.text_area(
        "Generated SITREP",
        value=sitrep_text,
        height=500
    )

    pdf_buffer = generate_pdf_sitrep(sitrep_text, reports_df)

    st.download_button(
        label="Download SITREP as PDF",
        data=pdf_buffer,
        file_name="e_warps_sitrep.pdf",
        mime="application/pdf"
    )

    log_activity("SITREP Generated", "Situation report viewed/generated")


# =========================
# RESOURCES
# =========================
elif page == "Resources":
    st.title("🚚 Resource Allocation Module")

    reports_df = load_reports()
    resources_df = load_resources()

    st.subheader("Available Resources")

    if not resources_df.empty:
        st.dataframe(resources_df, use_container_width=True)
    else:
        st.warning("No resources encoded yet.")

    with st.form("resource_form", clear_on_submit=True):
        resource_name = st.text_input("Resource Name", placeholder="Example: QRF Team, Ambulance, Rescue Vehicle")
        quantity = st.number_input("Available Quantity", min_value=0, value=0)
        resource_remarks = st.text_area("Remarks")

        submit_resource = st.form_submit_button("Save Resource")

    if submit_resource:
        save_resource(resource_name, quantity, resource_remarks)
        st.success("Resource saved.")
        st.rerun()

    st.divider()

    st.subheader("Suggested Allocation")

    allocation_text = generate_resource_recommendation(reports_df, resources_df)

    st.text_area(
        "AI-Assisted Resource Allocation Recommendation",
        value=allocation_text,
        height=400
    )

    st.divider()

    st.subheader("Edit/Delete Resource")

    if not resources_df.empty:
        selected_resource_id = st.selectbox(
            "Select Resource ID",
            resources_df["ID"].tolist()
        )

        selected_resource = resources_df[resources_df["ID"] == selected_resource_id].iloc[0]

        with st.form("edit_resource_form"):
            edited_resource_name = st.text_input("Resource Name", value=selected_resource["Resource"])
            edited_quantity = st.number_input("Quantity", min_value=0, value=int(selected_resource["Quantity"]))
            edited_remarks = st.text_area("Remarks", value=str(selected_resource["Remarks"]))

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


# =========================
# EDIT / DELETE REPORTS
# =========================
elif page == "Edit/Delete Reports":
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

        selected_report = reports_df[reports_df["ID"] == selected_report_id].iloc[0]

        with st.form("edit_report_form"):
            barangay = st.text_input("Barangay", value=selected_report["Barangay"])
            municipality = st.text_input("Municipality / City", value=selected_report["Municipality / City"])

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

            casualties = st.number_input("Casualties", min_value=0, value=int(selected_report["Casualties"]))
            injured = st.number_input("Injured", min_value=0, value=int(selected_report["Injured"]))
            trapped = st.number_input("Trapped Persons", min_value=0, value=int(selected_report["Trapped Persons"]))
            damaged_buildings = st.number_input("Damaged Buildings", min_value=0, value=int(selected_report["Damaged Buildings"]))

            road_status_options = ["Passable", "Partially Blocked", "Blocked"]

            road_status = st.selectbox(
                "Road Status",
                road_status_options,
                index=road_status_options.index(selected_report["Road Status"])
            )

            remarks = st.text_area("Remarks", value=str(selected_report["Remarks"]))

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
                    st.image(photo["filepath"], caption=photo["filename"], use_container_width=True)
        else:
            st.info("No photos uploaded for this report.")

        st.divider()

        if st.button("Delete Selected Report"):
            delete_report(selected_report_id)
            st.success("Report deleted.")
            st.rerun()


# =========================
# EXPORT REPORTS
# =========================
elif page == "Export Reports":
    st.title("📤 Export Reports")

    reports_df = load_reports()

    if not reports_df.empty:
        csv = reports_df.to_csv(index=False).encode("utf-8")

        st.dataframe(reports_df, use_container_width=True)

        st.download_button(
            label="Download Incident Reports as CSV",
            data=csv,
            file_name="e_warps_incident_reports.csv",
            mime="text/csv"
        )

        sitrep_text = generate_sitrep_text(reports_df, load_alerts())
        pdf_buffer = generate_pdf_sitrep(sitrep_text, reports_df)

        st.download_button(
            label="Download SITREP as PDF",
            data=pdf_buffer,
            file_name="e_warps_sitrep.pdf",
            mime="application/pdf"
        )

        st.info("Photos are saved in the uploads folder and are not included inside the CSV or PDF file.")

        log_activity("Reports Exported", "CSV/PDF export page accessed")

    else:
        st.warning("No reports available to export.")


# =========================
# ACTIVITY LOG
# =========================
elif page == "Activity Log":
    st.title("📜 Activity Log / Audit Trail")

    logs_df = load_activity_log()

    if not logs_df.empty:
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.warning("No activity logs recorded yet.")


# =========================
# SETTINGS
# =========================
elif page == "Settings":
    st.title("⚙️ Settings")

    st.warning("Use these buttons only for testing.")

    if st.button("Clear Incident Reports"):
        clear_reports()
        reset_incident_form()
        st.success("Incident reports and photos cleared.")

    if st.button("Clear Earthquake Alerts"):
        clear_alerts()
        reset_alert_form()
        st.success("Earthquake alerts cleared.")

    if st.button("Clear Resources"):
        clear_resources()
        st.success("Resources cleared.")

    if st.button("Clear Activity Log"):
        clear_activity_log()
        st.success("Activity log cleared.")

    if st.button("Clear All Data"):
        clear_reports()
        clear_alerts()
        clear_resources()
        clear_activity_log()
        reset_incident_form()
        reset_alert_form()
        st.success("All data cleared.")