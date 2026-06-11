import os
from datetime import datetime, timezone

import requests
from supabase import create_client


USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

# Rough Philippines bounding box
MIN_LATITUDE = 4.0
MAX_LATITUDE = 22.0
MIN_LONGITUDE = 116.0
MAX_LONGITUDE = 127.0

MIN_MAGNITUDE_TO_SAVE = 4.0


def get_secret_value(section, key):
    """
    Works both locally and in GitHub Actions.

    GitHub Actions uses environment variables:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY

    Local Streamlit app uses:
    .streamlit/secrets.toml
    """

    env_key = f"{section}_{key}".upper()

    if env_key in os.environ:
        return os.environ[env_key]

    try:
        import streamlit as st

        return st.secrets[section][key]

    except Exception as error:
        raise RuntimeError(
            f"Missing secret: {section}.{key}. "
            f"Set environment variable {env_key} or add it to Streamlit secrets."
        ) from error


def get_supabase_client():
    supabase_url = get_secret_value("supabase", "url")
    supabase_key = get_secret_value("supabase", "service_role_key")

    return create_client(
        supabase_url,
        supabase_key
    )


def is_inside_philippines_area(latitude, longitude):
    return (
        MIN_LATITUDE <= latitude <= MAX_LATITUDE
        and MIN_LONGITUDE <= longitude <= MAX_LONGITUDE
    )


def convert_usgs_time(milliseconds):
    if milliseconds is None:
        return ""

    seconds = milliseconds / 1000

    event_time = datetime.fromtimestamp(
        seconds,
        tz=timezone.utc
    )

    return event_time.astimezone().strftime(
        "%Y-%m-%d %I:%M %p"
    )


def fetch_usgs_earthquakes():
    response = requests.get(
        USGS_FEED_URL,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def save_alert_if_new(client, alert_data):
    source_event_id = alert_data["source_event_id"]

    existing_alert = (
        client.table("alerts")
        .select("id")
        .eq("source_event_id", source_event_id)
        .execute()
    )

    if existing_alert.data:
        return False

    client.table("alerts").insert(alert_data).execute()

    return True


def automate_earthquake_alerts():
    client = get_supabase_client()

    earthquake_data = fetch_usgs_earthquakes()

    features = earthquake_data.get("features", [])

    saved_count = 0
    skipped_count = 0

    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        coordinates = geometry.get("coordinates", [])

        if len(coordinates) < 3:
            skipped_count += 1
            continue

        longitude = float(coordinates[0])
        latitude = float(coordinates[1])
        depth = float(coordinates[2])

        magnitude = properties.get("mag")

        if magnitude is None:
            skipped_count += 1
            continue

        magnitude = float(magnitude)

        if magnitude < MIN_MAGNITUDE_TO_SAVE:
            skipped_count += 1
            continue

        if not is_inside_philippines_area(latitude, longitude):
            skipped_count += 1
            continue

        source_event_id = feature.get("id", "")

        if not source_event_id:
            skipped_count += 1
            continue

        place = properties.get("place", "Unknown location")
        event_time = convert_usgs_time(properties.get("time"))

        alert_data = {
            "source_event_id": source_event_id,
            "magnitude": magnitude,
            "epicenter": place,
            "depth": depth,
            "alert_time": event_time,
            "remarks": (
                f"Automated alert from USGS feed. "
                f"Coordinates: {latitude:.4f}, {longitude:.4f}"
            )
        }

        was_saved = save_alert_if_new(
            client,
            alert_data
        )

        if was_saved:
            saved_count += 1
        else:
            skipped_count += 1

    return saved_count, skipped_count


if __name__ == "__main__":
    saved_count, skipped_count = automate_earthquake_alerts()

    print("E-WARPS Automated Earthquake Alert Check")
    print(f"Saved new alerts: {saved_count}")
    print(f"Skipped existing/non-matching events: {skipped_count}")