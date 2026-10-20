# =============================================================================
# SDSe Fluid Design Studio - Landing Page
# =============================================================================

import streamlit as st


# =============================================================================
# CSS SPECIFIC TO LANDING PAGE
# =============================================================================

LANDING_CSS = """
    <style>
    /* Kill Streamlit's default top gap and lock scrolling */
    .stApp > header { display: none !important; }
    
    /* Lock the main container to the viewport height, no scrolling */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 420px;
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important;
        display: flex;
        flex-direction: column;
    }

    /* Center the top content naturally */
    .landing-top-content {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 0 0.5rem;
    }

    .landing-block {
        text-align: center;
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

    /* Bottom Section */
    .landing-bottom-content {
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
    }

    .landing-footer {
        font-size: 0.78rem;
        color: #a8b8c8;
        letter-spacing: 1px;
        text-align: center;
        margin-top: 0;
        margin-bottom: 0.8rem;
    }

    .landing-lab-divider {
        height: 1px;
        background-color: #1e2a3a;
        margin: 0.5rem auto 0.8rem auto;
        border: none;
        width: 100%;
        max-width: 220px;
    }
    
    .landing-lab-label {
        font-size: 0.72rem;
        color: #566073;
        letter-spacing: 1.5px;
        text-align: center;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }
    
    /* Tighten the Streamlit buttons so they fit perfectly */
    div[data-testid="stButton"] {
        width: 100%;
        margin-bottom: 0;
    }
    div[data-testid="stButton"] button {
        padding-top: 0.4rem !important;
        padding-bottom: 0.4rem !important;
    }
    </style>
"""


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_landing():
    """
    Render the landing page.
    """
    st.markdown(LANDING_CSS, unsafe_allow_html=True)

    # ---- 1. Top Content Wrapper (Grows to fill space and centers)
    st.markdown('<div class="landing-top-content">', unsafe_allow_html=True)
    
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

    st.markdown('</div>', unsafe_allow_html=True) # Close landing-top-content

    # ---- 2. Bottom Content Wrapper (Fixed to the bottom)
    st.markdown('<div class="landing-bottom-content">', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="landing-footer">All Major Building Code</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<hr class="landing-lab-divider">'
        '<div class="landing-lab-label">Internal</div>',
        unsafe_allow_html=True,
    )

    # ---- Lab button
    if st.button(
        "Lab",
        key="landing_lab",
        use_container_width=True,
    ):
        st.session_state.page = "lab"
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True) # Close landing-bottom-content
