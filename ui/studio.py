# =============================================================================
# SDSe Fluid Design Studio - Studio Page
# =============================================================================
# The structure type selection page. Appears after the user taps
# "Enter The Studio" on the landing page.
#
# Updated 2026-10-20:
#   - Removed redundant "Select" buttons.
#   - Made the structure description cards themselves clickable.
# =============================================================================

import streamlit as st

from data.structures import STRUCTURE_TYPES


# =============================================================================
# THE EIGHT FINAL STRUCTURE TYPES - IN TWO SECTIONS
# =============================================================================

STUDIO_SECTION_A = [
    "saddle_span",
    "cantilever",
    "multi_cone_roof",
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
    "multi_cone_roof": {
        "name": "Multi-Cone Roof",
        "icon": "M",
        "description": "Ridge beam with multiple cones, cable and fabric",
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
        margin-bottom: 0.2rem;
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
    
    /* Make the button invisible but stretch it over the card */
    div[data-testid="stButton"] {
        position: relative;
        top: -76px; /* Pulls the invisible button up over the card */
        height: 0px;
        z-index: 999;
    }
    div[data-testid="stButton"] > button {
        background-color: transparent !important;
        border: none !important;
        color: transparent !important;
        width: 100% !important;
        height: 76px !important; /* Matches card height */
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: rgba(243, 156, 18, 0.05) !important;
    }
    </style>
"""


# =============================================================================
# HELPERS
# =============================================================================

def _render_structure_tile(key):
    """Render one structure tile as a clickable card."""
    entry = STRUCTURE_TYPES.get(key, {})
    fallback = STUDIO_FALLBACK.get(key, {})

    name = entry.get("name", fallback.get("name", key))
    icon = entry.get("icon", fallback.get("icon", "?"))
    description = entry.get("description", fallback.get("description", ""))

    # 1. Draw the beautiful card
    tile_html = (
        '<div class="studio-tile">'
        f'<div class="studio-tile-icon">{icon}</div>'
        '<div class="studio-tile-body">'
        f'<div class="studio-tile-name">{name}</div>'
        f'<div class="studio-tile-desc">{description}</div>'
        '</div>'
        '</div>'
    )
    st.markdown(tile_html, unsafe_allow_html=True)

    # 2. The invisible button that sits on top of it
    # The CSS above hides the button box and pulls it up so it covers the card.
    if st.button(f"Select {name}", key="studio_select_" + key, use_container_width=True):
        st.session_state.structure_key = key
        st.session_state.structure_name = name
        st.session_state.page = "registration"
        st.rerun()


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
        'Select a structure to open the design workshop.'
        '</div>',
        unsafe_allow_html=True,
    )

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
