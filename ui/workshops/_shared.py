# =============================================================================
# SDSe Fluid Design Studio - Shared Workshop Helpers
# =============================================================================
# Common CSS and helper functions used by every workshop.
#
# Purpose:
#   - Keep each workshop file short (~200 lines) for safe iOS pasting
#   - One place to change styles across all workshops
#   - One place for shared widget helpers
#
# Used by:
#   ui/workshops/saddle_standard.py
#   ui/workshops/saddle_leaf.py
#   (and every future workshop)
#
# History:
#   2026-09-14 - Created after repeated iOS paste mangling on long
#                single-file workshop pastes. Extracting shared parts
#                makes every future paste shorter and safer.
# =============================================================================

import streamlit as st


# =============================================================================
# SHARED WORKSHOP CSS
# =============================================================================

WORKSHOP_CSS = """
    <style>
    .ws-breadcrumb {
        font-size: 0.85rem;
        color: #a8b8c8;
        margin-bottom: 1.2rem;
        letter-spacing: 0.3px;
    }
    .ws-breadcrumb .crumb {
        color: #f39c12;
        font-weight: 600;
    }
    .ws-section {
        background-color: #121e2e;
        border: 1px solid #1e2a3a;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
    }
    .ws-section-title {
        color: #f39c12;
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0 0 0.2rem 0;
        letter-spacing: 0.3px;
    }
    .ws-section-help {
        color: #a8b8c8;
        font-size: 0.82rem;
        margin: 0 0 0.8rem 0;
        line-height: 1.35;
    }
    .ws-preview-box {
        background-color: #0d1620;
        border-left: 3px solid #3498db;
        padding: 0.6rem 0.8rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #c8d4e0;
        line-height: 1.5;
    }
    .ws-preview-box .num {
        color: #ffffff;
        font-weight: 600;
    }
    .ws-warning-box {
        background-color: #4a3a1a;
        border-left: 3px solid #f39c12;
        padding: 0.6rem 0.8rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #f0f4fa;
    }
    .ws-info-box {
        background-color: #1a2a3a;
        border-left: 3px solid #4a7a9c;
        padding: 0.7rem 0.9rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #c8d4e0;
        line-height: 1.5;
    }
    </style>
"""


# =============================================================================
# SHARED HELPERS
# =============================================================================

def section_header(title, help_text=""):
    """Render a section header with custom amber styling."""
    html = '<div class="ws-section-title">' + title + '</div>'
    if help_text:
        html += '<div class="ws-section-help">' + help_text + '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_breadcrumb(structure_name, variant_name):
    """Render the standard workshop breadcrumb."""
    html = (
        '<div class="ws-breadcrumb">'
        'SDSe Fluid Design Studio / '
        '<span class="crumb">' + structure_name + '</span>'
        ' / '
        '<span class="crumb">' + variant_name + '</span>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_project_header(project_name, client_name, structure_label):
    """Render the project header card."""
    html = (
        '<div class="ws-section">'
        '<div class="ws-section-title">' + project_name + '</div>'
        '<div class="ws-section-help">'
        'Client: ' + client_name + '  |  Structure: ' + structure_label +
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def info_box(text):
    """Render a blue info box."""
    st.markdown(
        '<div class="ws-info-box">' + text + '</div>',
        unsafe_allow_html=True,
    )


def preview_box(text):
    """Render a blue preview box."""
    st.markdown(
        '<div class="ws-preview-box">' + text + '</div>',
        unsafe_allow_html=True,
    )


def warning_box(text):
    """Render an amber warning box."""
    st.markdown(
        '<div class="ws-warning-box">' + text + '</div>',
        unsafe_allow_html=True,
    )


def apply_typical_foundation_defaults(prefix):
    """
    Apply typical suburban soil/foundation values to session state.
    Also clears the widget keys so Streamlit recreates the widgets
    with the new values on the next rerun.

    Streamlit note:
      Widget keys are separate from state keys. Deleting the widget
      key forces Streamlit to rebuild the widget from the state
      value on the next rerun.
    """
    st.session_state[prefix + "_soil_bearing"] = 150.0
    st.session_state[prefix + "_soil_type"] = "sand"
    st.session_state[prefix + "_water_table"] = 3.0
    st.session_state[prefix + "_foundation_type"] = "pad"

    widget_keys = [
        prefix + "_soil_bearing_input",
        prefix + "_water_table_input",
        prefix + "_soil_type_select",
        prefix + "_found_type_select",
    ]
    for k in widget_keys:
        if k in st.session_state:
            del st.session_state[k]
