import streamlit as st

from config import (
    ROLE_PAGES,
    ensure_upload_folder,
    ensure_assets_folder
)
from database import initialize_database
from ui import (
    apply_custom_css,
    show_app_header,
    show_footer_note,
    show_login_header
)

from app_pages.dashboard import show_dashboard
from app_pages.about import show_about
from app_pages.earthquake_alerts import show_earthquake_alerts
from app_pages.incident_reports import show_incident_reports
from app_pages.prioritization import show_prioritization
from app_pages.gis_map import show_gis_map
from app_pages.command_recommendations import show_command_recommendations
from app_pages.situation_report import show_situation_report
from app_pages.resources import show_resources
from app_pages.edit_delete_reports import show_edit_delete_reports
from app_pages.export_reports import show_export_reports
from app_pages.activity_log import show_activity_log
from app_pages.settings import show_settings


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="E-WARPS",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_custom_css()

ensure_upload_folder()
ensure_assets_folder()
initialize_database()


# =========================
# USERS FROM SECRETS
# =========================
def get_users():
    try:
        return dict(st.secrets["users"])

    except Exception:
        return {
            "admin": {
                "password": "admin123",
                "name": "System Administrator",
                "role": "Admin"
            },
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
            }
        }


USERS = get_users()


# =========================
# SESSION STATE
# =========================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "login_error" not in st.session_state:
    st.session_state.login_error = ""

if "username" not in st.session_state:
    st.session_state.username = ""

if "display_name" not in st.session_state:
    st.session_state.display_name = ""

if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Dashboard"

if "navigation_page" not in st.session_state:
    st.session_state.navigation_page = "Dashboard"

if "pending_page" not in st.session_state:
    st.session_state.pending_page = None

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
# LOGIN / LOGOUT FUNCTIONS
# =========================
def complete_login(username):
    user_record = USERS[username]

    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.display_name = user_record["name"]
    st.session_state.user_role = user_record["role"]
    st.session_state.selected_page = "Dashboard"
    st.session_state.navigation_page = "Dashboard"
    st.session_state.pending_page = None
    st.session_state.login_error = ""


def login_user(username, password):
    clean_username = username.strip().lower()

    if clean_username in USERS:
        user_record = USERS[clean_username]

        if password == user_record["password"]:
            complete_login(clean_username)
            return

    st.session_state.login_error = "Invalid username or password."


def demo_login(username):
    if username in USERS:
        complete_login(username)


def logout_user():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.display_name = ""
    st.session_state.user_role = "Commander"
    st.session_state.selected_page = "Dashboard"
    st.session_state.navigation_page = "Dashboard"
    st.session_state.pending_page = None


# =========================
# LOGIN SCREEN
# =========================
if not st.session_state.authenticated:
    left_col, center_col, right_col = st.columns([1, 1.2, 1])

    with center_col:
        show_login_header()

        st.markdown("### Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submit_login = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if submit_login:
            login_user(username, password)

            if st.session_state.authenticated:
                st.rerun()

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

        st.divider()

        st.markdown("### Demo Mode")
        st.caption("Use these buttons for quick system demonstration.")

        demo_col1, demo_col2 = st.columns(2)

        with demo_col1:
            if st.button("Login as Admin", use_container_width=True):
                demo_login("admin")
                st.rerun()

            if st.button("Login as Commander", use_container_width=True):
                demo_login("commander")
                st.rerun()

        with demo_col2:
            if st.button("Login as Operations Officer", use_container_width=True):
                demo_login("ops")
                st.rerun()

            if st.button("Login as Responder", use_container_width=True):
                demo_login("responder")
                st.rerun()

    st.stop()


# =========================
# CALLBACKS
# =========================
def update_selected_page():
    st.session_state.selected_page = st.session_state.navigation_page


# =========================
# SIDEBAR
# =========================
st.sidebar.title("🌏 E-WARPS")

st.sidebar.markdown(
    f"""
    <div class="user-badge">
        <div class="user-badge-row">
            <span class="user-label">User</span>
            <span class="user-value">{st.session_state.display_name}</span>
        </div>
        <div class="user-badge-row">
            <span class="user-label">Role</span>
            <span class="user-value">{st.session_state.user_role}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if st.sidebar.button("Logout", use_container_width=True):
    logout_user()
    st.rerun()

pages = ROLE_PAGES.get(
    st.session_state.user_role,
    ROLE_PAGES["Admin"]
)

if st.session_state.pending_page is not None:
    requested_page = st.session_state.pending_page

    if requested_page in pages:
        st.session_state.selected_page = requested_page
        st.session_state.navigation_page = requested_page

    st.session_state.pending_page = None

if st.session_state.selected_page not in pages:
    st.session_state.selected_page = pages[0]

if st.session_state.navigation_page not in pages:
    st.session_state.navigation_page = st.session_state.selected_page

st.sidebar.radio(
    "Navigation",
    pages,
    index=pages.index(st.session_state.selected_page),
    key="navigation_page",
    on_change=update_selected_page
)

page = st.session_state.selected_page


# =========================
# MAIN APP HEADER
# =========================
show_app_header()


# =========================
# PAGE ROUTER
# =========================
if page == "Dashboard":
    show_dashboard()

elif page == "About / System Information":
    show_about()

elif page == "Earthquake Alerts":
    show_earthquake_alerts()

elif page == "Incident Reports":
    show_incident_reports()

elif page == "Prioritization":
    show_prioritization()

elif page == "GIS Map":
    show_gis_map()

elif page == "Command Recommendations":
    show_command_recommendations()

elif page == "Situation Report":
    show_situation_report()

elif page == "Resources":
    show_resources()

elif page == "Edit/Delete Reports":
    show_edit_delete_reports()

elif page == "Export Reports":
    show_export_reports()

elif page == "Activity Log":
    show_activity_log()

elif page == "Settings":
    show_settings()


# =========================
# FOOTER
# =========================
show_footer_note()