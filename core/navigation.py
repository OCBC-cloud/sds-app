"""SDSe — Navigation.

Maps page names to renderer functions.
All pages must be registered in PAGE_RENDERERS.
"""

import streamlit as st


DEFAULT_PAGE = "landing"


# =============================================================================
# PAGE RENDERERS
# =============================================================================

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


def _render_lab():
    from ui.lab import render_lab
    render_lab()


def _render_tester_multi_cone():
    from ui.workshops.tester_multi_cone import render_tester_multi_cone
    render_tester_multi_cone()


def _render_SDSe_analysis_report():
    from ui.workshops.SDSe_analysis_report import render_SDSe_analysis_report
    render_SDSe_analysis_report()


def _render_mesh_z_diagnostic():
    from ui.mesh_z_diagnostic import render_mesh_z_diagnostic
    render_mesh_z_diagnostic()


# =============================================================================
# PAGE REGISTRY
# =============================================================================

PAGE_RENDERERS = {
    "landing": _render_landing,
    "studio": _render_studio,
    "registration": _render_registration,
    "workshop": _render_workshop,
    "results": _render_results,
    "lab": _render_lab,
    "tester_multi_cone": _render_tester_multi_cone,
    "analysis_report": _render_SDSe_analysis_report,
    "mesh_z_diagnostic": _render_mesh_z_diagnostic,
}


# =============================================================================
# DISPATCHER
# =============================================================================

def render_current_page():
    """Dispatch to the renderer for the current page."""
    page = st.session_state.get("page", DEFAULT_PAGE)
    renderer = PAGE_RENDERERS.get(page)

    if renderer is None:
        st.session_state.page = DEFAULT_PAGE
        renderer = PAGE_RENDERERS[DEFAULT_PAGE]

    renderer()
