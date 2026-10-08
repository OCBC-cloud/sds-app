# =============================================================================
# SDSe Fluid Design Studio - Lab Page
# =============================================================================
# Internal test pages. Not linked from the landing page.
# To reach the Lab, set st.session_state.page = "lab" from a Python
# session, or type the page in the URL once routing is exposed.
#
# The Lab is where experimental pages live while they are being built.
# Nothing in the Lab is production-ready. Nothing in the Lab is visible
# to a customer.
#
# History:
#   2026-10-08 - First version. MBS Tester and Renderer Test moved
#                here from the landing page.
# =============================================================================

import streamlit as st


# =============================================================================
# CSS SPECIFIC TO LAB PAGE
# =============================================================================

LAB_CSS = """
    <style>
    .stApp > header { display: none !important; }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 640px;
    }

    .lab-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 0 0.6rem 0;
        border-bottom: 1px solid #1e2a3a;
        margin-bottom: 1.2rem;
    }
    .lab-wordmark {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f39c12;
        letter-spacing: 2px;
    }
    .lab-section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0.4rem 0 0.3rem 0;
    }
    .lab-section-sub {
        font-size: 0.9rem;
        color: #a8b8c8;
        margin-bottom: 1.2rem;
        line-height: 1.4;
    }
    .lab-tile {
        background-color: #121e2e;
        border: 1px solid #1e2a3a;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.7rem;
    }
    .lab-tile-name {
        font-size: 1rem;
        font-weight: 600;
        color: #ffffff;
        margin: 0 0 0.25rem 0;
    }
    .lab-tile-desc {
        font-size: 0.85rem;
        color: #a8b8c8;
        margin: 0;
        line-height: 1.35;
    }
    </style>
"""


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_lab():
    """
    Render the Lab page. Internal test pages only.
    Called by the navigation router when st.session_state.page == 'lab'.
    """
    st.markdown(LAB_CSS, unsafe_allow_html=True)

    # ---- Top bar
    st.markdown(
        '<div class="lab-topbar">'
        '<div class="lab-wordmark">SDSe LAB</div>'
        '<div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Header
    st.markdown(
        '<div class="lab-section-header">Internal Test Pages</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="lab-section-sub">'
        'Experimental pages, in progress. Nothing in the Lab is '
        'production-ready. Nothing in the Lab is visible to a customer.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- MBS Tester
    st.markdown(
        '<div class="lab-tile">'
        '<div class="lab-tile-name">MBS Tester</div>'
        '<div class="lab-tile-desc">'
        'The experimental MBS engine. Used for testing new shapes '
        'and new solver behaviour.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("Open MBS Tester", key="lab_tester_mbs", use_container_width=True):
        st.session_state.page = "tester_mbs"
        st.rerun()

    # ---- Renderer Test
    st.markdown(
        '<div class="lab-tile">'
        '<div class="lab-tile-name">Renderer Test</div>'
        '<div class="lab-tile-desc">'
        'Test page for the Plotly renderer. Used to check new '
        'geometry generation without running the full App flow.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("Open Renderer Test", key="lab_renderer_test", use_container_width=True):
        st.session_state.page = "renderer_test"
        st.rerun()

    # ---- Placeholder for future test pages
    st.markdown(
        '<div class="lab-tile" style="opacity: 0.5;">'
        '<div class="lab-tile-name">(more test pages may be added here)</div>'
        '<div class="lab-tile-desc">'
        'The Lab is where experimental pages live while they are '
        'being built.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Back to Landing
    st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
    if st.button("Back to Landing", key="lab_back", use_container_width=True):
        st.session_state.page = "landing"
        st.rerun()
