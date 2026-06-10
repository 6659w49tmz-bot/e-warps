import os

DB_FILE = "ewarps.db"
UPLOAD_FOLDER = "uploads"
ASSETS_FOLDER = "assets"
LOGO_FILE = os.path.join(ASSETS_FOLDER, "logo.png")

ROLE_OPTIONS = [
    "Commander",
    "Operations Officer",
    "Responder",
    "Admin"
]

ALL_PAGES = [
    "Dashboard",
    "About / System Information",
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

ROLE_PAGES = {
    "Commander": [
        "Dashboard",
        "About / System Information",
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
        "About / System Information",
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
        "About / System Information",
        "Incident Reports",
        "GIS Map"
    ],
    "Admin": ALL_PAGES
}

# Simple prototype users.
# For capstone demo only. Later, this can be moved to SQLite with hashed passwords.
USERS = {
    "commander": {
        "password": "commander123",
        "name": "Commander",
        "role": "Commander"
    },
    "ops": {
        "password": "ops123",
        "name": "Operations Officer",
        "role": "Operations Officer"
    },
    "responder": {
        "password": "responder123",
        "name": "Field Responder",
        "role": "Responder"
    },
    "admin": {
        "password": "admin123",
        "name": "System Administrator",
        "role": "Admin"
    },
    "reybernales": {
        "password": "@Berns2210",
        "name": "2LT REY ANTHONY F BERNALES (CE) PA",
        "role": "Admin"
    }
}


def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)


def ensure_assets_folder():
    if not os.path.exists(ASSETS_FOLDER):
        os.makedirs(ASSETS_FOLDER)