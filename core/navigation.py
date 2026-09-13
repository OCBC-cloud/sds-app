# =============================================================================
# SDSe Fluid Design Studio - Navigation Router
# =============================================================================

import streamlit as st


DEFAULT_PAGE = "landing"


def _render_landing():
    from ui.landing import render_landing
    render_landing()


def _render_studio():
    from ui.studio import render_studio
    render_studio()


def _render_registration():
    from ui.registration import render_registration
    render_registration()


def _render_workshop():
    from ui.workshop import render_workshop
    render_workshop()


def _render_results():
    from ui.results import render_results
    render_results()


def _render_guided():
    st.markdown(
        '<div style="background-color: #1a2a3a; border-left: 4px solid #f39c12; '
        'border-radius: 8px; padding: 1.5rem; margin: 2rem 0; text-align: center;">'
        '<div style="color: #f39c12; font-size: 1.2rem; font-weight: 700; '
        'margin-bottom: 0.5rem;">Smart Guided Design</div>'
        '<div style="color: #c8d4e0; font-size: 0.95rem; line-height: 1.5;">'
        'Coming soon. Please return to Studio and pick a structure directly.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("Back to Studio", key="guided_back", use_container_width=True):
        st.session_state.page = "studio"
        st.rerun()


PAGE_RENDERERS = {
    "landing": _render_landing,
    "studio": _render_studio,
    "registration": _render_registration,
    "workshop": _render_workshop,
    "results": _render_results,
    "guided": _render_guided,
}


def render_current_page():
    page = st.session_state.get("page", DEFAULT_PAGE)
    renderer = PAGE_RENDERERS.get(page, None)
    if renderer is None:
        st.session_state.page = DEFAULT_PAGE
        renderer = PAGE_RENDERERS[DEFAULT_PAGE]
    renderer()
