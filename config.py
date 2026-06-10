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
    "Settings",
    "About / System Information"
]


ROLE_PAGES = {
    "Commander": [
        "Dashboard",
        "Prioritization",
        "GIS Map",
        "Command Recommendations",
        "Situation Report",
        "Resources",
        "Export Reports",
        "Activity Log",
        "About / System Information"
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
        "Activity Log",
        "About / System Information"
    ],
    "Responder": [
        "Dashboard",
        "Incident Reports",
        "GIS Map",
        "Situation Report",
        "About / System Information"
    ],
    "Admin": ALL_PAGES
}


def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)


def ensure_assets_folder():
    if not os.path.exists(ASSETS_FOLDER):
        os.makedirs(ASSETS_FOLDER)