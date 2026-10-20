# =============================================================================
# SDSe Fluid Design Studio - Studio Page
# =============================================================================
# The structure type selection page.
#
# Updated 2026-10-20:
#   - Completely removed the HTML cards and invisible overlays.
#   - Styled native Streamlit buttons to look exactly like the cards.
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

    /* 
     * THE TRICK: Style the native Streamlit buttons to look like the cards.
     * We use the key prefix "studio_select_" to target only these buttons.
     */
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #121e2e !important;
        border: 1px solid #1e2a3a !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        text-align: left !important;
        height: auto !important;
        min-height: 85px !important;
        transition: all 0.25s ease !important;
        display: flex !important;
        justify-content: flex-start !important;
    }
    
    /* Hover state */
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: #f39c12 !important;
        box-shadow: 0 4px 16px rgba(243, 156, 18, 0.15) !important;
        color: white !important;
        background-color: #121e2e !important;
    }

    /* Force the button text to be white and stacked */
    div[data-testid="stButton"] button[kind="secondary"] p {
        color: #ffffff !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }
    
    /* The description below the title */
    div[data-testid="stButton"] button[kind="secondary"] span {
        color: #a8b8c8 !important;
        font-size: 0.85rem !important;
        font-weight: 400 !important;
        display: block !important;
        margin-top: 4px !important;
        white-space: normal !important;
        text-align: left !important;
    }
    </style>
"""


# =============================================================================
# HELPERS
# =============================================================================

def _render_structure_tile(key):
    """Render one structure tile as a styled native button."""
    entry = STRUCTURE_TYPES.get(key, {})
    fallback = STUDIO_FALLBACK.get(key, {})

    name = entry.get("name", fallback.get("name", key))
    icon = entry.get("icon", fallback.get("icon", "?"))
    description = entry.get("description", fallback.get("description", ""))

    # We use markdown to format the button label so it has two lines:
    # Line 1: Name
    # Line 2: Description (smaller)
    # (We use the icon as a prefix in the name)
    
    button_label = f"**{icon} | {name}**\n\n{description}"

    if st.button(button_label, key="studio_select_" + key, use_container_width=True):
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
