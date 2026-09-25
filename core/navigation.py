# =============================================================================
# SDSe Fluid Design Studio - Navigation Router
# =============================================================================
# Routes the current page to its render function.
#
# Updated 2026-09-15:
#   - Added leaf_room route for Rib Length Adjustment room
# Updated 2026-09-25:
#   - Removed tester_nfdm route (experimental).
#   - Added tester_mbs route (experimental, MBS engine test).
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


def _render_leaf_room():
    from ui.rooms.leaf_room import render_leaf_room
    render_leaf_room()


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


def _render_tester_mbs():
    from ui.workshops.tester_mbs import render_tester_mbs
    render_tester_mbs()


PAGE_RENDERERS = {
    "landing": _render_landing,
    "studio": _render_studio,
    "registration": _render_registration,
    "workshop": _render_workshop,
    "results": _render_results,
    "leaf_room": _render_leaf_room,
    "guided": _render_guided,
    "tester_mbs": _render_tester_mbs,
}


def render_current_page():
    page = st.session_state.get("page", DEFAULT_PAGE)
    renderer = PAGE_RENDERERS.get(page, None)
    if renderer is None:
        st.session_state.page = DEFAULT_PAGE
        renderer = PAGE_RENDERERS[DEFAULT_PAGE]
    renderer()





