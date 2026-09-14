# =============================================================================
# SDSe Fluid Design Studio - Studio Page
# =============================================================================
# The structure type selection page. Appears after the user taps
# "Enter The Studio" on the landing page.
#
# Design (agreed 2026-09-13, tightened 2026-09-14):
#   - 8 structure type tiles across 2 sections
#   - "Smart Guided Design" tile at the top
#   - Small SDSe wordmark top-left
#   - Section header "Choose Your Structure Type"
#   - No back button (landing is a splash screen)
#   - Each tile: icon + name + one-line description
#   - Tapping a structure type advances to Registration
#   - Tapping Guided Design starts the wizard (placeholder for now)
#   - Top gap trimmed to match landing page tightness
# =============================================================================

import streamlit as st

from data.structures import STRUCTURE_TYPES


# =============================================================================
# THE EIGHT FINAL STRUCTURE TYPES - IN TWO SECTIONS
# =============================================================================

STUDIO_SECTION_A = [
    "saddle_span",
    "cantilever",
    "unipole_tensile",
    "tensile_sails",
    "framed_tensile",
]

STUDIO_SECTION_B = [
    "canopy",
    "frame_tent",
    "portal_frame",
]


# =============================================================================
# FALLBACK NAMES AND DESCRIPTIONS
# =============================================================================

STUDIO_FALLBACK = {
    "saddle_span": {
        "name": "Saddle Span",
        "icon": "S",
        "description": "Curved saddle-shaped tensile structure",
    },
    "cantilever": {
        "name": "Cantilever",
        "icon": "L",
        "description": "Single column with arm and membrane",
    },
    "unipole_tensile": {
        "name": "Uni-Pole Tensile Roof",
        "icon": "U",
        "description": "Mast with radial membrane",
    },
    "tensile_sails": {
        "name": "Tensile Sails Roof",
        "icon": "T",
        "description": "Hypar sails spanning between anchors",
    },
    "framed_tensile": {
        "name": "Framed Tensile Roof",
        "icon": "R",
        "description": "Fabric on rigid frame",
    },
    "canopy": {
        "name": "Canopy",
        "icon": "C",
        "description": "Wall-mounted, cable-supported, or tree shade",
    },
    "frame_tent": {
        "name": "Frame Tent",
        "icon": "F",
        "description": "Framed tent structure",
    },
    "portal_frame": {
        "name": "Portal Frame",
        "icon": "P",
        "description": "Rigid steel frame structure",
    },
}


# =============================================================================
# CSS SPECIFIC TO STUDIO PAGE
# =============================================================================

STUDIO_CSS = """
    <style>
    /* Trim Streamlit's default top gap on the studio page */
    .stApp > header { display: none !important; }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 640px;
    }

    .studio-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 0 0.6rem 0;
        border-bottom: 1px solid #1e2a3a;
        margin-bottom: 1.2rem;
    }
    .studio-wordmark {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f39c12;
        letter-spacing: 2px;
    }
    .studio-section-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0.4rem 0 0.3rem 0;
        letter-spacing: 0.5px;
    }
    .studio-section-sub {
        font-size: 0.9rem;
        color: #a8b8c8;
        margin-bottom: 1.2rem;
    }
    .studio-subsection-header {
        font-size: 1.05rem;
        font-weight: 700;
        color: #f39c12;
        margin: 1.4rem 0 0.7rem 0;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        border-bottom: 1px solid #1e2a3a;
        padding-bottom: 0.5rem;
    }

    /* Structure type tiles */
    .studio-tile {
        display: flex;
        align-items: center;
        gap: 1rem;
        background-color: #121e2e;
        border: 1px solid #1e2a3a;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.7rem;
        transition: all 0.25s ease;
    }
    .studio-tile:hover {
        border-color: #f39c12;
        transform: translateX(4px);
        box-shadow: 0 4px 16px rgba(243, 156, 18, 0.15);
    }
    .studio-tile-icon {
        width: 52px;
        height: 52px;
        min-width: 52px;
        border-radius: 50%;
        background-color: rgba(243, 156, 18, 0.12);
        border: 2px solid #f39c12;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 700;
        color: #f39c12;
    }
    .studio-tile-body {
        flex: 1;
        text-align: left;
    }
    .studio-tile-name {
        font-size: 1.05rem;
        font-weight: 600;
        color: #ffffff;
        margin: 0 0 0.25rem 0;
    }
    .studio-tile-desc {
        font-size: 0.85rem;
        color: #a8b8c8;
        margin: 0;
        line-height: 1.35;
    }

    /* Guided Design tile - visually distinct */
    .guided-tile {
        display: flex;
        align-items: center;
        gap: 1rem;
        background: linear-gradient(90deg, #f39c12 0%, #f1c40f 100%);
        border-radius: 12px;
        padding: 1.2rem 1.2rem;
        margin-bottom: 1.4rem;
        transition: all 0.25s ease;
        border: none;
    }
    .guided-tile:hover {
        transform: translateX(4px);
        box-shadow: 0 6px 24px rgba(243, 156, 18, 0.35);
    }
    .guided-tile-icon {
        width: 52px;
        height: 52px;
        min-width: 52px;
        border-radius: 50%;
        background-color: rgba(10, 14, 23, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.6rem;
        font-weight: 700;
        color: #0a0e17;
    }
    .guided-tile-body {
        flex: 1;
        text-align: left;
    }
    .guided-tile-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0a0e17;
        margin: 0 0 0.2rem 0;
    }
    .guided-tile-desc {
        font-size: 0.85rem;
        color: #0a0e17;
        margin: 0;
        line-height: 1.35;
        opacity: 0.85;
    }
    </style>
"""


# =============================================================================
# HELPERS
# =============================================================================

def _render_structure_tile(key):
    """Render one structure tile plus its Select button."""
    entry = STRUCTURE_TYPES.get(key, {})
    fallback = STUDIO_FALLBACK.get(key, {})

    name = entry.get("name", fallback.get("name", key))
    icon = entry.get("icon", fallback.get("icon", "?"))
    description = entry.get("description", fallback.get("description", ""))

    tile_html = (
        '<div class="studio-tile">'
        '<div class="studio-tile-icon">' + icon + '</div>'
        '<div class="studio-tile-body">'
        '<div class="studio-tile-name">' + name + '</div>'
        '<div class="studio-tile-desc">' + description + '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(tile_html, unsafe_allow_html=True)

    if st.button("Select " + name, key="studio_select_" + key, use_container_width=True):
        st.session_state.structure_key = key
        st.session_state.structure_name = name
        st.session_state.page = "registration"
        st.rerun()

    st.markdown('<div style="height: 0.2rem;"></div>', unsafe_allow_html=True)


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_studio():
    """
    Render the Studio page.
    Called by the navigation router when the app state is 'studio'.
    """
    st.markdown(STUDIO_CSS, unsafe_allow_html=True)

    # ---- Top bar with wordmark
    st.markdown(
        '<div class="studio-topbar">'
        '<div class="studio-wordmark">SDSe</div>'
        '<div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Main section header
    st.markdown(
        '<div class="studio-section-header">Choose Your Structure Type</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="studio-section-sub">'
        'Select a structure to open the design workshop. '
        'Or use the guided path to be recommended one.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Guided Design tile
    guided_html = (
        '<div class="guided-tile">'
        '<div class="guided-tile-icon">?</div>'
        '<div class="guided-tile-body">'
        '<div class="guided-tile-name">Smart Guided Design</div>'
        '<div class="guided-tile-desc">'
        'Answer a few questions and we will recommend the best structure for you.'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(guided_html, unsafe_allow_html=True)

    if st.button("Start Guided Design", key="studio_guided", use_container_width=True, type="primary"):
        st.session_state.page = "guided"
        st.rerun()

    st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

    # ---- Section A: Tensile and Membrane
    st.markdown(
        '<div class="studio-subsection-header">Tensile and Membrane</div>',
        unsafe_allow_html=True,
    )
    for key in STUDIO_SECTION_A:
        _render_structure_tile(key)

    # ---- Section B: Canopy and Frame
    st.markdown(
        '<div class="studio-subsection-header">Canopy and Frame</div>',
        unsafe_allow_html=True,
    )
    for key in STUDIO_SECTION_B:
        _render_structure_tile(key)
