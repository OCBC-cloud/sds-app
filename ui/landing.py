# =============================================================================
# SDSe Fluid Design Studio - Landing Page
# =============================================================================
# The first page a user sees.
#
# Purpose: impact page. Introduce the app. One button in.
# Sets the design tone for the whole app.
#
# Design (agreed 2026-09-12, simplified 2026-09-14):
#   - Dark base #0a0e17
#   - Accent orange #f39c12
#   - Logo badge, title, subtitle, brand, button, footer
#   - Single HTML block to avoid Streamlit's block padding
#   - Button is the only Streamlit widget on the page
#   - No flexbox, no vh units, no min-height
#   - Layout adapts to any phone screen naturally
#
# Updated 2026-09-23:
#   - Added temporary NFDM Tester button. Experimental. Reachable
#     only from this landing page. Delete this button + the tester
#     workshop + engine/nfdm.py + the tester_nfdm route in
#     core/navigation.py to remove the tester entirely.
# =============================================================================

import streamlit as st


# =============================================================================
# CSS SPECIFIC TO LANDING PAGE
# =============================================================================

LANDING_CSS = """
    <style>
    /* Kill Streamlit's default top gap on the landing page */
    .stApp > header { display: none !important; }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0 !important;
        max-width: 420px;
    }

    .landing-block {
        text-align: center;
        padding: 1rem 0.5rem 0 0.5rem;
    }

    .landing-logo {
        width: 84px;
        height: 84px;
        border: 2px solid #f39c12;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1.2rem auto;
        color: #f39c12;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 1px;
    }

    .landing-title {
        font-size: 3.2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 2px;
        margin: 0;
        line-height: 1;
    }

    .landing-sub {
        font-size: 1rem;
        color: #c8d4e0;
        letter-spacing: 1.5px;
        margin-top: 0.9rem;
        margin-bottom: 0;
        line-height: 1.5;
        font-weight: 400;
    }

    .landing-divider {
        width: 60px;
        height: 2px;
        background-color: #f39c12;
        margin: 1.6rem auto 1.6rem auto;
        border: none;
        border-radius: 1px;
    }

    .landing-brand {
        font-size: 0.9rem;
        color: #f39c12;
        letter-spacing: 2px;
        text-transform: none;
        font-weight: 600;
        margin: 0 0 2rem 0;
    }

    .landing-footer {
        font-size: 0.78rem;
        color: #a8b8c8;
        letter-spacing: 1px;
        text-align: center;
        margin-top: 1rem;
    }

    .landing-test-label {
        font-size: 0.7rem;
        color: #7a8fa8;
        letter-spacing: 1px;
        text-align: center;
        margin-top: 1.4rem;
        margin-bottom: 0.3rem;
        text-transform: uppercase;
    }
    </style>
"""


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_landing():
    """
    Render the landing page.
    Called by the navigation router when the app state is 'landing'.
    """
    st.markdown(LANDING_CSS, unsafe_allow_html=True)

    # ---- One single HTML block for everything except the buttons
    landing_html = (
        '<div class="landing-block">'
        '<div class="landing-logo">SDSe</div>'
        '<div class="landing-title">SDSe</div>'
        '<div class="landing-sub">Intelligent Fluid Design<br>Workplace</div>'
        '<hr class="landing-divider">'
        '<div class="landing-brand">SDSe Fluid Design Studio</div>'
        '</div>'
    )
    st.markdown(landing_html, unsafe_allow_html=True)

    # ---- Primary button
    if st.button(
        "Enter The Studio",
        key="landing_enter",
        use_container_width=True,
        type="primary",
    ):
        st.session_state.page = "studio"
        st.rerun()

    # ---- Temporary experimental button: NFDM tester
    st.markdown(
        '<div class="landing-test-label">Experimental</div>',
        unsafe_allow_html=True,
    )
    if st.button(
        "Open NFDM Tester",
        key="landing_tester",
        use_container_width=True,
        type="secondary",
    ):
        st.session_state.page = "tester_nfdm"
        st.rerun()

    # ---- Footer
    st.markdown(
        '<div class="landing-footer">All Major Building Code</div>',
        unsafe_allow_html=True,
    )





