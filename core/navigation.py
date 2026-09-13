# =============================================================================
# SDSe Fluid Design Studio - Navigation Router
# =============================================================================
# Reads st.session_state.page and dispatches to the correct render function.
#
# Pages:
#   landing      -> ui.landing.render_landing()
#   studio       -> ui.studio.render_studio()
#   registration -> ui.registration.render_registration()
#   workshop     -> ui.workshop.render_workshop()
#   results      -> ui.results.render_results()
#   guided       -> placeholder (Smart Guided Design wizard, not yet built)
#
# Design decisions (agreed 2026-09-13):
#   - Landing is the default page if none is set
#   - Landing is a one-way door - Home always returns to Studio
#   - Returning to Studio resets structure_key and variant_key
#   - Unknown pages fall back to landing
# =============================================================================

import streamlit as st


# =============================================================================
# PAGE DEFAULTS
# =============================================================================

DEFAULT_PAGE = "landing"


# =============================================================================
# RENDERERS
# =============================================================================
# Import each renderer lazily to avoid circular imports and speed up startup.

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
    """Placeholder for the Smart Guided Design wizard (not yet built)."""
    st.markdown(
        '<div style="background-color: #1a2a3a; border-left: 4px solid #f39c12; '
        'border-radius: 8px; padding: 1.5rem; margin: 2rem 0; text-align: center;">'
        '<div style="color: #f39c12; font-size: 1.2rem; font-weight: 700; '
        'margin-bottom: 0.5rem;">Smart Guided Design</div>'
        '<div style="color: #c8d4e0; font-size: 0.95rem; line-height: 1.5;">'
        'The guided design wizard is being built. '
        'Please return to the Studio and choose a structure type directly.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
    if st.button("Back to Studio", key="guided_back", use_container_width=True):
        st.session_state.page = "studio"
        st.rerun()


# =============================================================================
# ROUTER
# =============================================================================

PAGE_RENDERERS = {
    "landing": _render_landing,
    "studio": _render_studio,
    "registration": _render_registration,
    "workshop": _render_workshop,
    "results": _render_results,
    "guided": _render_guided,
}


def render_current_page():
    """
    Read st.session_state.page and render the corresponding page.
    Defaults to landing if the page is unset or unknown.
    """
    page = st.session_state.get("page", DEFAULT_PAGE)

    renderer = PAGE_RENDERERS.get(page, None)

    if renderer is None:
        # Unknown page - fall back to landing
        st.session_state.page = DEFAULT_PAGE
        renderer = PAGE_RENDERERS[DEFAULT_PAGE]

    renderer()


# =============================================================================
# NAVIGATION HELPERS
# =============================================================================
# Small helpers used by pages to move between screens and manage state.

def goto_landing():
    """Return to the landing page."""
    st.session_state.page = "landing"
    st.rerun()


def goto_studio():
    """
    Return to the Studio.
    Resets structure_key and variant_key so the user starts fresh.
    """
    if "structure_key" in st.session_state:
        del st.session_state["structure_key"]
    if "structure_name" in st.session_state:
        del st.session_state["structure_name"]
    if "variant_key" in st.session_state:
        del st.session_state["variant_key"]
    if "variant_name" in st.session_state:
        del st.session_state["variant_name"]
    st.session_state.page = "studio"
    st.rerun()


def goto_registration(structure_key, structure_name):
    """Advance to Registration for a chosen structure type."""
    st.session_state.structure_key = structure_key
    st.session_state.structure_name = structure_name
    st.session_state.page = "registration"
    st.rerun()


def goto_workshop(variant_key, variant_name):
    """Advance to Workshop for a chosen variant."""
    st.session_state.variant_key = variant_key
    st.session_state.variant_name = variant_name
    st.session_state.page = "workshop"
    st.rerun()


def goto_results():
    """Advance to Results."""
    st.session_state.page = "results"
    st.rerun()


def goto_guided():
    """Start the Smart Guided Design wizard."""
    st.session_state.page = "guided"
    st.rerun()
