import os
import uuid
import tempfile

import pandas as pd
import requests
import streamlit as st
from supabase import create_client


# =========================
# SUPABASE CONNECTION
# =========================
def get_supabase_client():
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["service_role_key"]

        return create_client(
            supabase_url,
            supabase_key
        )

    except Exception as error:
        st.error(
            "Supabase connection is not configured. "
            "Please check Streamlit Secrets."
        )
        st.exception(error)
        return None


def get_storage_bucket():
    try:
        return st.secrets["supabase"]["bucket"]

    except Exception:
        return "incident-photos"


def initialize_database():
    # Tables are already created in Supabase SQL Editor.
    # This function remains here because app.py calls it.
    return


# =========================
# PHOTO TEMP FILE HELPER
# =========================
def download_photo_to_temp(public_url, storage_path):
    if not public_url:
        return ""

    try:
        file_name = os.path.basename(storage_path)

        if not file_name:
            file_name = f"{uuid.uuid4()}.jpg"

        temp_folder = os.path.join(
            tempfile.gettempdir(),
            "ewarps_photos"
        )

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        temp_path = os.path.join(
            temp_folder,
            file_name
        )

        if os.path.exists(temp_path):
            return temp_path

        response = requests.get(
            public_url,
            timeout=15
        )

        if response.status_code == 200:
            with open(temp_path, "wb") as file:
                file.write(response.content)

            return temp_path

        return public_url

    except Exception:
        return public_url


# =========================
# ACTIVITY LOG
# =========================
def log_activity(action, details=""):
    client = get_supabase_client()

    if client is None:
        return

    user_role = st.session_state.get(
        "user_role",
        "Unknown"
    )

    client.table("activity_log").insert(
        {
            "action": action,
            "details": details,
            "user_role": user_role
        }
    ).execute()


def load_activity_log():
    client = get_supabase_client()

    columns = [
        "ID",
        "Action",
        "Details",
        "User Role",
        "Date/Time"
    ]

    if client is None:
        return pd.DataFrame(columns=columns)

    response = client.table("activity_log").select("*").order(
        "created_at",
        desc=True
    ).execute()

    rows = response.data or []

    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows)

    df = df.rename(
        columns={
            "id": "ID",
            "action": "Action",
            "details": "Details",
            "user_role": "User Role",
            "created_at": "Date/Time"
        }
    )

    return df[columns]


def clear_activity_log():
    client = get_supabase_client()

    if client is None:
        return

    client.table("activity_log").delete().gt(
        "id",
        0
    ).execute()


# =========================
# EARTHQUAKE ALERTS
# =========================
def save_alert(magnitude, epicenter, depth, alert_time, remarks):
    client = get_supabase_client()

    if client is None:
        return

    client.table("alerts").insert(
        {
            "magnitude": magnitude,
            "epicenter": epicenter,
            "depth": depth,
            "alert_time": alert_time,
            "remarks": remarks
        }
    ).execute()

    log_activity(
        "Earthquake Alert Saved",
        f"Magnitude {magnitude} at {epicenter}"
    )


def load_alerts():
    client = get_supabase_client()

    columns = [
        "ID",
        "Magnitude",
        "Epicenter",
        "Depth",
        "Date/Time",
        "Remarks",
        "Created At"
    ]

    if client is None:
        return pd.DataFrame(columns=columns)

    response = client.table("alerts").select("*").order(
        "created_at",
        desc=True
    ).execute()

    rows = response.data or []

    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows)

    df = df.rename(
        columns={
            "id": "ID",
            "magnitude": "Magnitude",
            "epicenter": "Epicenter",
            "depth": "Depth",
            "alert_time": "Date/Time",
            "remarks": "Remarks",
            "created_at": "Created At"
        }
    )

    return df[columns]


def clear_alerts():
    client = get_supabase_client()

    if client is None:
        return

    client.table("alerts").delete().gt(
        "id",
        0
    ).execute()

    log_activity(
        "Earthquake Alerts Cleared",
        "All earthquake alerts were cleared"
    )


# =========================
# INCIDENT REPORTS
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
    score,
    priority,
    remarks,
    uploaded_photos
):
    client = get_supabase_client()
    bucket = get_storage_bucket()

    if client is None:
        return None

    report_response = client.table("reports").insert(
        {
            "barangay": barangay,
            "municipality": municipality,
            "latitude": latitude,
            "longitude": longitude,
            "casualties": casualties,
            "injured": injured,
            "trapped": trapped,
            "damaged_buildings": damaged_buildings,
            "road_status": road_status,
            "priority_score": score,
            "priority": priority,
            "remarks": remarks
        }
    ).execute()

    report_rows = report_response.data or []

    if not report_rows:
        return None

    report_id = report_rows[0]["id"]

    if uploaded_photos:
        for uploaded_photo in uploaded_photos:
            original_filename = uploaded_photo.name
            file_extension = os.path.splitext(original_filename)[1]

            if not file_extension:
                file_extension = ".jpg"

            storage_filename = f"{uuid.uuid4()}{file_extension}"
            storage_path = f"report_{report_id}/{storage_filename}"

            file_bytes = uploaded_photo.getvalue()
            content_type = uploaded_photo.type or "application/octet-stream"

            client.storage.from_(bucket).upload(
                path=storage_path,
                file=file_bytes,
                file_options={
                    "content-type": content_type
                }
            )

            public_url = client.storage.from_(bucket).get_public_url(
                storage_path
            )

            client.table("photos").insert(
                {
                    "report_id": report_id,
                    "filename": original_filename,
                    "storage_path": storage_path,
                    "public_url": public_url
                }
            ).execute()

    log_activity(
        "Incident Report Saved",
        f"{barangay}, {municipality} - {priority}"
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
    score,
    priority,
    remarks
):
    client = get_supabase_client()

    if client is None:
        return

    client.table("reports").update(
        {
            "barangay": barangay,
            "municipality": municipality,
            "latitude": latitude,
            "longitude": longitude,
            "casualties": casualties,
            "injured": injured,
            "trapped": trapped,
            "damaged_buildings": damaged_buildings,
            "road_status": road_status,
            "priority_score": score,
            "priority": priority,
            "remarks": remarks
        }
    ).eq(
        "id",
        report_id
    ).execute()

    log_activity(
        "Incident Report Updated",
        f"Report ID {report_id} updated"
    )


def delete_report(report_id):
    client = get_supabase_client()
    bucket = get_storage_bucket()

    if client is None:
        return

    photos_response = client.table("photos").select("*").eq(
        "report_id",
        report_id
    ).execute()

    photos = photos_response.data or []

    storage_paths = []

    for photo in photos:
        storage_path = photo.get("storage_path")

        if storage_path:
            storage_paths.append(storage_path)

    if storage_paths:
        client.storage.from_(bucket).remove(storage_paths)

    client.table("reports").delete().eq(
        "id",
        report_id
    ).execute()

    log_activity(
        "Incident Report Deleted",
        f"Report ID {report_id} deleted"
    )


def load_reports():
    client = get_supabase_client()

    columns = [
        "ID",
        "Barangay",
        "Municipality / City",
        "Latitude",
        "Longitude",
        "Casualties",
        "Injured",
        "Trapped Persons",
        "Damaged Buildings",
        "Road Status",
        "Priority Score",
        "Priority",
        "Remarks",
        "Date/Time"
    ]

    if client is None:
        return pd.DataFrame(columns=columns)

    response = client.table("reports").select("*").order(
        "priority_score",
        desc=True
    ).execute()

    rows = response.data or []

    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows)

    df = df.rename(
        columns={
            "id": "ID",
            "barangay": "Barangay",
            "municipality": "Municipality / City",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "casualties": "Casualties",
            "injured": "Injured",
            "trapped": "Trapped Persons",
            "damaged_buildings": "Damaged Buildings",
            "road_status": "Road Status",
            "priority_score": "Priority Score",
            "priority": "Priority",
            "remarks": "Remarks",
            "created_at": "Date/Time"
        }
    )

    return df[columns]


def load_photos(report_id):
    client = get_supabase_client()

    columns = [
        "ID",
        "report_id",
        "filename",
        "filepath",
        "storage_path",
        "public_url",
        "Created At"
    ]

    if client is None:
        return pd.DataFrame(columns=columns)

    response = client.table("photos").select("*").eq(
        "report_id",
        report_id
    ).order(
        "created_at",
        desc=False
    ).execute()

    rows = response.data or []

    if not rows:
        return pd.DataFrame(columns=columns)

    prepared_rows = []

    for row in rows:
        public_url = row.get("public_url", "")
        storage_path = row.get("storage_path", "")

        temp_or_url_path = download_photo_to_temp(
            public_url,
            storage_path
        )

        prepared_rows.append(
            {
                "ID": row.get("id"),
                "report_id": row.get("report_id"),
                "filename": row.get("filename"),
                "filepath": temp_or_url_path,
                "storage_path": storage_path,
                "public_url": public_url,
                "Created At": row.get("created_at")
            }
        )

    return pd.DataFrame(prepared_rows)


def clear_reports():
    client = get_supabase_client()
    bucket = get_storage_bucket()

    if client is None:
        return

    photos_response = client.table("photos").select("*").execute()
    photos = photos_response.data or []

    storage_paths = []

    for photo in photos:
        storage_path = photo.get("storage_path")

        if storage_path:
            storage_paths.append(storage_path)

    if storage_paths:
        client.storage.from_(bucket).remove(storage_paths)

    client.table("photos").delete().gt(
        "id",
        0
    ).execute()

    client.table("reports").delete().gt(
        "id",
        0
    ).execute()

    log_activity(
        "Incident Reports Cleared",
        "All incident reports and photos were cleared"
    )


# =========================
# RESOURCES
# =========================
def save_resource(resource_name, available_quantity, remarks):
    client = get_supabase_client()

    if client is None:
        return

    client.table("resources").insert(
        {
            "resource_name": resource_name,
            "available_quantity": available_quantity,
            "remarks": remarks
        }
    ).execute()

    log_activity(
        "Resource Saved",
        f"{resource_name} saved"
    )


def load_resources():
    client = get_supabase_client()

    columns = [
        "ID",
        "Resource",
        "Quantity",
        "Remarks",
        "Created At"
    ]

    if client is None:
        return pd.DataFrame(columns=columns)

    response = client.table("resources").select("*").order(
        "created_at",
        desc=True
    ).execute()

    rows = response.data or []

    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows)

    df = df.rename(
        columns={
            "id": "ID",
            "resource_name": "Resource",
            "available_quantity": "Quantity",
            "remarks": "Remarks",
            "created_at": "Created At"
        }
    )

    return df[columns]


def update_resource(resource_id, resource_name, available_quantity, remarks):
    client = get_supabase_client()

    if client is None:
        return

    client.table("resources").update(
        {
            "resource_name": resource_name,
            "available_quantity": available_quantity,
            "remarks": remarks
        }
    ).eq(
        "id",
        resource_id
    ).execute()

    log_activity(
        "Resource Updated",
        f"Resource ID {resource_id} updated"
    )


def delete_resource(resource_id):
    client = get_supabase_client()

    if client is None:
        return

    client.table("resources").delete().eq(
        "id",
        resource_id
    ).execute()

    log_activity(
        "Resource Deleted",
        f"Resource ID {resource_id} deleted"
    )


def clear_resources():
    client = get_supabase_client()

    if client is None:
        return

    client.table("resources").delete().gt(
        "id",
        0
    ).execute()

    log_activity(
        "Resources Cleared",
        "All resources were cleared"
    )