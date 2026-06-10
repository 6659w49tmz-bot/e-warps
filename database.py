import os
import uuid
import sqlite3
import pandas as pd
from datetime import datetime

import streamlit as st

from config import DB_FILE, UPLOAD_FOLDER


# =========================
# CONNECTION
# =========================
def get_connection():
    return sqlite3.connect(DB_FILE)


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    for column in columns:
        if column[1] == column_name:
            return True

    return False


# =========================
# DATABASE INITIALIZATION
# =========================
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


# =========================
# ACTIVITY LOG
# =========================
def log_activity(action, details=""):
    conn = get_connection()
    cursor = conn.cursor()

    user_role = st.session_state.get("user_role", "Unknown")

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
            user_role,
            action,
            details
        )
    )

    conn.commit()
    conn.close()


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


def clear_activity_log():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM activity_log")

    conn.commit()
    conn.close()


# =========================
# ALERTS
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

    log_activity(
        "Earthquake Alert Saved",
        f"Magnitude {magnitude}, Epicenter {epicenter}"
    )


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


def clear_alerts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM alerts")

    conn.commit()
    conn.close()

    log_activity(
        "All Earthquake Alerts Cleared",
        "All alerts removed"
    )


# =========================
# REPORTS
# =========================
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

    log_activity(
        "Incident Report Saved",
        f"{barangay}, {municipality}, Priority: {priority}"
    )

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

    log_activity(
        "Incident Report Updated",
        f"Report ID {report_id}, {barangay}, Priority: {priority}"
    )


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

    log_activity(
        "Incident Report Deleted",
        f"Report ID {report_id}"
    )


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


def clear_reports():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM photos")
    cursor.execute("DELETE FROM reports")

    conn.commit()
    conn.close()

    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            if os.path.isfile(filepath):
                os.remove(filepath)

    log_activity(
        "All Incident Reports Cleared",
        "All reports and uploaded photos removed"
    )


# =========================
# RESOURCES
# =========================
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

    log_activity(
        "Resource Added",
        f"{resource_name}: {available_quantity}"
    )


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

    log_activity(
        "Resource Updated",
        f"{resource_name}: {available_quantity}"
    )


def delete_resource(resource_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM resources WHERE id = ?",
        (resource_id,)
    )

    conn.commit()
    conn.close()

    log_activity(
        "Resource Deleted",
        f"Resource ID {resource_id}"
    )


def clear_resources():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM resources")

    conn.commit()
    conn.close()

    log_activity(
        "All Resources Cleared",
        "All resources removed"
    )