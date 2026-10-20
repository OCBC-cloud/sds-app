# =============================================================================
# SDSe Fluid Design Studio - Studio Page
# =============================================================================

import streamlit as st

from data.structures import STRUCTURE_TYPES

STUDIO_SECTION_A = [
    "saddle_span", "cantilever", "multi_cone_roof", "tensile_sails", "framed_tensile"
]

STUDIO_SECTION_B = [
    "canopy", "frame_tent", "portal_frame"
]

STUDIO_FALLBACK = {
    "saddle_span": {"name": "Saddle Span", "description": "Curved saddle-shaped tensile structure"},
    "cantilever": {"name": "Cantilever", "description": "Single column with arm and membrane"},
    "multi_cone_roof": {"name": "Multi-Cone Roof", "description": "Ridge beam with multiple cones, cable and fabric"},
    "tensile_sails": {"name": "Tensile Sails Roof", "description": "Hypar sails spanning between anchors"},
    "framed_tensile": {"name": "Framed Tensile Roof", "description": "Fabric on rigid frame"},
    "canopy": {"name": "Canopy", "description": "Wall-mounted, cable-supported, or tree shade"},
    "frame_tent": {"name": "Frame Tent", "description": "Framed tent structure"},
    "portal_frame": {"name": "Portal Frame", "description": "Rigid steel frame structure"},
}

STUDIO_CSS = """
    <style>
    /* Tighten the entire page container */
    .stApp > header { display: none !important; }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 640px;
    }

    /* Compress headers */
    .studio-topbar {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0 0 0.2rem 0; border-bottom: 1px solid #1e2a3a; margin-bottom: 0.5rem;
    }
    .studio-wordmark { font-size: 1.0rem; font-weight: 700; color: #f39c12; letter-spacing: 2px; }
    
    .studio-section-header { 
        font-size: 1.3rem; font-weight: 700; color: #ffffff; 
        margin: 0.2rem 0 0.1rem 0; letter-spacing: 0.5px; 
    }
    .studio-section-sub { 
        font-size: 0.85rem; color: #a8b8c8; margin-bottom: 0.8rem; 
    }
    .studio-subsection-header {
        font-size: 0.95rem; font-weight: 700; color: #f39c12; 
        margin: 0.8rem 0 0.5rem 0; letter-spacing: 0.8px; 
        text-transform: uppercase; border-bottom: 1px solid #1e2a3a; padding-bottom: 0.3rem;
    }

    /* Make the buttons very compact */
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #121e2e !important;
        border: 1px solid #1e2a3a !important;
        border-radius: 8px !important;
        padding: 0.4rem 0.8rem !important;
        height: 65px !important;
        min-height: 65px !important;
        max-height: 65px !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
    }
    
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: #f39c12 !important;
        background-color: #121e2e !important;
    }

    /* Compact the text inside the buttons */
    div[data-testid="stButton"] button[kind="secondary"] p {
        text-align: center !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    div[data-testid="stButton"] button[kind="secondary"] p:nth-of-type(1) {
        color: #ffffff !important;
        font-size: 1.0rem !important;
        font-weight: 600 !important;
        margin-bottom: 0px !important;
        line-height: 1.1 !important;
    }
    
    div[data-testid="stButton"] button[kind="secondary"] p:nth-of-type(2) {
        color: #a8b8c8 !important;
        font-size: 0.75rem !important;
        font-weight: 400 !important;
        line-height: 1.1 !important;
    }
    
    /* Remove the default Streamlit gap between buttons */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0rem !important;
    }
    
    /* Add a tiny custom gap */
    div[data-testid="stButton"] {
        margin-bottom: 0.3rem !important;
    }

    /* Owner-only Lab section at the bottom */
    .studio-lab-divider {
        height: 1px;
        background-color: #1e2a3a;
        margin: 1.5rem auto 0.8rem auto;
        border: none;
        width: 100%;
    }
    .studio-lab-label {
        font-size: 0.72rem;
        color: #566073;
        letter-spacing: 1.5px;
        text-align: center;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
    }
    </style>
"""

def _render_structure_tile(key):
    entry = STRUCTURE_TYPES.get(key, {})
    fallback = STUDIO_FALLBACK.get(key, {})
    name = entry.get("name", fallback.get("name", key))
    description = entry.get("description", fallback.get("description", ""))

    button_label = f"**{name}**\n{description}"

    if st.button(button_label, key="studio_select_" + key, use_container_width=True):
        st.session_state.structure_key = key
        st.session_state.structure_name = name
        st.session_state.page = "registration"
        st.rerun()

def render_studio():
    st.markdown(STUDIO_CSS, unsafe_allow_html=True)

    st.markdown('<div class="studio-topbar"><div class="studio-wordmark">SDSe</div><div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="studio-section-header">Choose Your Structure Type</div>', unsafe_allow_html=True)
    st.markdown('<div class="studio-section-sub">Select a structure to open the design workshop.</div>', unsafe_allow_html=True)

    st.markdown('<div class="studio-subsection-header">Tensile and Membrane</div>', unsafe_allow_html=True)
    for key in STUDIO_SECTION_A:
        _render_structure_tile(key)

    st.markdown('<div class="studio-subsection-header">Canopy and Frame</div>', unsafe_allow_html=True)
    for key in STUDIO_SECTION_B:
        _render_structure_tile(key)

    # ---- Owner-Only Lab Section ----
    access_mode = str(st.session_state.get("access_mode", "owner")).lower()
    if access_mode == "owner":
        st.markdown(
            '<hr class="studio-lab-divider">'
            '<div class="studio-lab-label">Internal</div>',
            unsafe_allow_html=True,
        )
        if st.button("Lab", key="studio_lab", use_container_width=True):
            st.session_state.page = "lab"
            st.rerun()
