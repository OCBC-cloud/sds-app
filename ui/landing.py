# =============================================================================
# SDSe Fluid Design Studio - Landing Page
# =============================================================================
# The first page a user sees.
#
# Purpose: impact page. Introduce the app. One button in. No scrolling.
# Sets the design tone for the whole app.
#
# Design (agreed 2026-09-12, tightened 2026-09-14):
#   - Dark base #0a0e17
#   - Accent orange #f39c12
#   - Large title "SDSe"
#   - Subtitle "Intelligent Fluid Design Workplace"
#   - Brand line "SDSe Fluid Design Studio"
#   - Single button "Enter The Studio"
#   - Footer "All Major EN Code"
#   - Icon/emblem placeholder (to be replaced later)
#   - Everything fits on one phone screen, no scrolling
# =============================================================================

import streamlit as st


# =============================================================================
# CSS SPECIFIC TO LANDING PAGE
# =============================================================================

LANDING_CSS = """
    <style>
    /* Kill Streamlit's default top gap on the landing page */
    .stApp > header { display: none !important; }
    .block-container { padding-top: 0 !important; }

    /* Landing container, vertically centred, sized to fit one screen */
    .landing-wrap {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        min-height: 70vh;
        padding: 0.5rem 1rem;
    }

    .landing-logo-placeholder {
        width: 80px;
        height: 80px;
        border: 2px solid #f39c12;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1.2rem;
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

    .landing-subtitle {
        font-size: 1rem;
        color: #c8d4e0;
        letter-spacing: 1.5px;
        margin-top: 0.8rem;
        margin-bottom: 0.15rem;
        font-weight: 400;
    }

    .landing-subtitle-2 {
        font-size: 1rem;
        color: #c8d4e0;
        letter-spacing: 1.5px;
        margin-top: 0;
        margin-bottom: 1.2rem;
        font-weight: 400;
    }

    .landing-divider {
        width: 60px;
        height: 2px;
        background-color: #f39c12;
        margin: 0 auto 1.5rem auto;
        border: none;
        border-radius: 1px;
    }

    .landing-brand {
        font-size: 0.9rem;
        color: #f39c12;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 2rem;
    }

    .landing-footer {
        font-size: 0.78rem;
        color: #a8b8c8;
        letter-spacing: 1px;
        margin-top: 1.5rem;
        text-align: center;
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

    # Everything inside a centred wrapper (including the button)
    st.markdown('<div class="landing-wrap">', unsafe_allow_html=True)

    # Logo placeholder (circle with initials) - to be replaced with a real emblem later
    st.markdown(
        '<div class="landing-logo-placeholder">SDSe</div>',
        unsafe_allow_html=True,
    )

    # Main title
    st.markdown('<div class="landing-title">SDSe</div>', unsafe_allow_html=True)

    # Subtitle - two lines
    st.markdown(
        '<div class="landing-subtitle">Intelligent Fluid Design</div>'
        '<div class="landing-subtitle-2">Workplace</div>',
        unsafe_allow_html=True,
    )

    # Accent divider
    st.markdown('<hr class="landing-divider">', unsafe_allow_html=True)

    # Brand line
    st.markdown(
        '<div class="landing-brand">SDSe Fluid Design Studio</div>',
        unsafe_allow_html=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # Button in a narrow column, centred
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        if st.button(
            "Enter The Studio",
            key="landing_enter",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.page = "studio"
            st.rerun()

    # Footer
    st.markdown(
        '<div class="landing-footer">All Major EN Code</div>',
        unsafe_allow_html=True,
    )
