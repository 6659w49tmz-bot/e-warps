import streamlit as st
import os

from config import LOGO_FILE


# =========================
# CUSTOM CSS
# =========================
def apply_custom_css():
    st.markdown(
        """
        <style>
        /* =========================
           Hide Streamlit Cloud UI
        ========================= */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        header {
            visibility: hidden;
        }

        [data-testid="stToolbar"] {
            display: none !important;
            visibility: hidden !important;
        }

        [data-testid="stDecoration"] {
            display: none !important;
            visibility: hidden !important;
        }

        [data-testid="stStatusWidget"] {
            display: none !important;
            visibility: hidden !important;
        }

        [data-testid="stHeader"] {
            display: none !important;
            visibility: hidden !important;
        }

        .stDeployButton {
            display: none !important;
            visibility: hidden !important;
        }

        .viewerBadge_container__1QSob {
            display: none !important;
            visibility: hidden !important;
        }

        .viewerBadge_link__1S137 {
            display: none !important;
            visibility: hidden !important;
        }

        .viewerBadge_text__1JaDK {
            display: none !important;
            visibility: hidden !important;
        }

        /* Hide GitHub/Fork/toolbar-like buttons */
        a[href*="github.com"] {
            display: none !important;
            visibility: hidden !important;
        }

        button[title="View app source"] {
            display: none !important;
            visibility: hidden !important;
        }

        button[title="Fork this app"] {
            display: none !important;
            visibility: hidden !important;
        }

        button[title="Main menu"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* =========================
           General App Styling
        ========================= */
        .main {
            padding-top: 0rem;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        h1, h2, h3 {
            font-weight: 700;
        }

        .small-muted {
            color: #8a8f98;
            font-size: 0.9rem;
        }

        .section-card {
            padding: 1.2rem;
            border-radius: 16px;
            border: 1px solid rgba(128, 128, 128, 0.2);
            background: rgba(250, 250, 250, 0.04);
            margin-bottom: 1rem;
        }

        .metric-card {
            padding: 1rem;
            border-radius: 16px;
            border: 1px solid rgba(128, 128, 128, 0.2);
            background: rgba(250, 250, 250, 0.04);
            text-align: center;
        }

        .metric-title {
            font-size: 0.9rem;
            color: #8a8f98;
            margin-bottom: 0.25rem;
        }

        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
        }

        /* =========================
           Login Styling
        ========================= */
        .login-logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 1.2rem;
        }

        .login-logo {
            width: 150px;
            height: auto;
            border-radius: 14px;
        }

        .login-title {
            text-align: center;
            font-size: 2.4rem;
            font-weight: 800;
            margin-bottom: 0.4rem;
        }

        .login-subtitle {
            text-align: center;
            color: #8a8f98;
            font-size: 1rem;
            margin-bottom: 2rem;
        }

        /* =========================
           Header Styling
        ========================= */
        .app-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.5rem 0rem 1.2rem 0rem;
        }

        .app-header-logo {
            width: 70px;
            height: auto;
            border-radius: 12px;
        }

        .app-header-title {
            font-size: 2rem;
            font-weight: 800;
            margin: 0;
        }

        .app-header-subtitle {
            color: #8a8f98;
            font-size: 0.95rem;
            margin-top: 0.2rem;
        }

        /* =========================
           Sidebar User Badge
        ========================= */
        .user-badge {
            padding: 0.85rem;
            border-radius: 14px;
            border: 1px solid rgba(128, 128, 128, 0.25);
            background: rgba(250, 250, 250, 0.05);
            margin-bottom: 1rem;
        }

        .user-badge-row {
            display: flex;
            flex-direction: column;
            margin-bottom: 0.5rem;
        }

        .user-badge-row:last-child {
            margin-bottom: 0;
        }

        .user-label {
            font-size: 0.75rem;
            color: #8a8f98;
            text-transform: uppercase;
            letter-spacing: 0.04rem;
        }

        .user-value {
            font-size: 0.95rem;
            font-weight: 600;
            color: inherit;
        }

        /* =========================
           Sidebar Navigation Buttons
        ========================= */
        section[data-testid="stSidebar"] button {
            border-radius: 10px !important;
            border: 1px solid rgba(128, 128, 128, 0.25) !important;
            text-align: left !important;
            justify-content: flex-start !important;
        }

        section[data-testid="stSidebar"] button:hover {
            border-color: rgba(255, 75, 75, 0.7) !important;
        }

        /* =========================
           Priority Styling
        ========================= */
        .priority-high {
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 75, 75, 0.15);
            color: #ff4b4b;
            font-weight: 700;
        }

        .priority-medium {
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 193, 7, 0.15);
            color: #d99a00;
            font-weight: 700;
        }

        .priority-low {
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background: rgba(40, 167, 69, 0.15);
            color: #28a745;
            font-weight: 700;
        }

        /* =========================
           Status Legend Styling
        ========================= */
        .status-legend {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        }

        .legend-item {
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            border: 1px solid rgba(128, 128, 128, 0.25);
            font-size: 0.85rem;
            font-weight: 600;
        }

        .legend-high {
            background: rgba(255, 75, 75, 0.15);
            color: #ff4b4b;
        }

        .legend-medium {
            background: rgba(255, 193, 7, 0.15);
            color: #d99a00;
        }

        .legend-low {
            background: rgba(40, 167, 69, 0.15);
            color: #28a745;
        }

        .legend-alert {
            background: rgba(255, 140, 0, 0.15);
            color: #ff8c00;
        }

        /* =========================
           Mobile Adjustments
        ========================= */
        @media only screen and (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .login-title {
                font-size: 2rem;
            }

            .app-header-title {
                font-size: 1.5rem;
            }

            .app-header-subtitle {
                font-size: 0.85rem;
            }

            .app-header-logo {
                width: 55px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# =========================
# LOGO HELPERS
# =========================
def show_logo(width=120):
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=width)


def show_login_header():
    if os.path.exists(LOGO_FILE):
        st.markdown(
            '<div class="login-logo-container">',
            unsafe_allow_html=True
        )

        st.image(LOGO_FILE, width=150)

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <div class="login-title">E-WARPS Login</div>
        <div class="login-subtitle">
            AI-Assisted Earthquake Alert Integration, Damage Assessment,<br>
            Rescue Prioritization, and Command Decision Support System
        </div>
        """,
        unsafe_allow_html=True
    )


def show_app_header():
    col1, col2 = st.columns([0.8, 6])

    with col1:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, width=70)

    with col2:
        st.markdown(
            """
            <div class="app-header-title">E-WARPS</div>
            <div class="app-header-subtitle">
                AI-Assisted Earthquake Alert Integration, Damage Assessment,
                Rescue Prioritization, and Command Decision Support System
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()


# =========================
# PAGE TITLE HELPERS
# =========================
def show_page_title(title, subtitle=None):
    st.markdown(f"# {title}")

    if subtitle:
        st.markdown(
            f"<div class='small-muted'>{subtitle}</div>",
            unsafe_allow_html=True
        )

    st.write("")


def show_section_title(title):
    st.markdown(f"### {title}")


def show_footer_note():
    st.divider()

    st.caption(
        "E-WARPS Version 1 | AI-assisted disaster response support prototype"
    )


# =========================
# STATUS / PRIORITY HELPERS
# =========================
def show_priority_badge(priority):
    if priority == "High":
        badge_class = "priority-high"
    elif priority == "Medium":
        badge_class = "priority-medium"
    else:
        badge_class = "priority-low"

    st.markdown(
        f"<span class='{badge_class}'>{priority}</span>",
        unsafe_allow_html=True
    )


def show_status_legend():
    st.markdown(
        """
        <div class="status-legend">
            <span class="legend-item legend-high">High Priority</span>
            <span class="legend-item legend-medium">Medium Priority</span>
            <span class="legend-item legend-low">Low Priority</span>
            <span class="legend-item legend-alert">Earthquake Alert</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_empty_state(message):
    st.info(message)


def show_success_message(message):
    st.success(message)


def show_warning_message(message):
    st.warning(message)


def show_error_message(message):
    st.error(message)