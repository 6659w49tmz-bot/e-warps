import os
import base64

import streamlit as st

from config import LOGO_FILE


def get_logo_base64():
    if not os.path.exists(LOGO_FILE):
        return None

    with open(LOGO_FILE, "rb") as logo_file:
        encoded_logo = base64.b64encode(logo_file.read()).decode()

    return encoded_logo


def apply_custom_css():
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0rem;
        }

        .subtitle {
            font-size: 1rem;
            color: #A0A0A0;
            margin-top: 0.25rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }

        .command-banner {
            padding: 1.5rem 2rem;
            border-radius: 0.75rem;
            background: linear-gradient(90deg, #172554, #1e293b);
            border: 1px solid #334155;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1.75rem;
            min-height: 160px;
        }

        .command-logo {
            width: 130px;
            height: 130px;
            object-fit: contain;
            border-radius: 0.75rem;
            background-color: rgba(255,255,255,0.08);
            padding: 0.45rem;
        }

        .command-logo-fallback {
            font-size: 4rem;
        }

        .command-banner-text h1 {
            color: white;
            margin-bottom: 0.4rem;
            font-size: 2.7rem;
            font-weight: 900;
        }

        .command-banner-text p {
            color: #E2E8F0;
            margin-top: 0rem;
            font-size: 1.08rem;
            font-weight: 700;
            line-height: 1.6;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 800;
            margin-top: 1rem;
            margin-bottom: 0.75rem;
        }

        .footer-note {
            font-size: 0.85rem;
            color: #94A3B8;
            border-top: 1px solid #334155;
            padding-top: 0.75rem;
            margin-top: 2rem;
        }

        .login-box {
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid #334155;
            background-color: #111827;
            margin-top: 1rem;
        }

        .user-badge {
            padding: 0.8rem 0.9rem;
            border-radius: 0.65rem;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(148, 163, 184, 0.18);
            margin: 0.35rem 0 0.9rem 0;
        }

        .user-badge-row {
            margin-bottom: 0.55rem;
        }

        .user-badge-row:last-child {
            margin-bottom: 0;
        }

        .user-label {
            display: block;
            font-size: 0.72rem;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.15rem;
            font-weight: 700;
        }

        .user-value {
            display: block;
            font-size: 0.92rem;
            color: #E5E7EB;
            font-weight: 600;
            line-height: 1.4;
            word-break: break-word;
        }

        @media (max-width: 768px) {
            .command-banner {
                flex-direction: column;
                align-items: flex-start;
                padding: 1.25rem;
            }

            .command-logo {
                width: 110px;
                height: 110px;
            }

            .command-banner-text h1 {
                font-size: 2.2rem;
            }

            .command-banner-text p {
                font-size: 0.95rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def show_app_header():
    logo_base64 = get_logo_base64()

    if logo_base64:
        logo_html = f'<img class="command-logo" src="data:image/png;base64,{logo_base64}">'
    else:
        logo_html = '<div class="command-logo-fallback">🌏</div>'

    banner_html = f'''
<div class="command-banner">
    {logo_html}
    <div class="command-banner-text">
        <h1>E-WARPS</h1>
        <p><b>AI-Assisted Earthquake Alert Integration, Damage Assessment, Rescue Prioritization, and Command Decision Support System</b></p>
    </div>
</div>
'''

    st.markdown(
        banner_html,
        unsafe_allow_html=True
    )


def show_login_header():
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=150)
    else:
        st.markdown("# 🌏")

    st.markdown("# E-WARPS Login")
    st.caption(
        "AI-Assisted Earthquake Alert Integration, Damage Assessment, Rescue Prioritization, and Command Decision Support System"
    )


def show_page_title(title, subtitle=None):
    st.markdown(
        f"<div class='main-title'>{title}</div>",
        unsafe_allow_html=True
    )

    if subtitle:
        st.markdown(
            f"<div class='subtitle'>{subtitle}</div>",
            unsafe_allow_html=True
        )

    st.divider()


def show_section_title(title):
    st.markdown(
        f"<div class='section-title'>{title}</div>",
        unsafe_allow_html=True
    )


def show_footer_note():
    st.markdown(
        """
        <div class="footer-note">
            <b>Note:</b> E-WARPS recommendations are AI-assisted and advisory only. Final approval and operational decisions remain under authorized human command.
        </div>
        """,
        unsafe_allow_html=True
    )


def show_status_legend():
    st.markdown("### Priority Legend")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.error("🔴 **CRITICAL**")

    with col2:
        st.warning("🟠 **SEVERE**")

    with col3:
        st.info("🟡 **MODERATE**")

    with col4:
        st.success("🟢 **LOW**")