# =============================================================================
# SDSe Fluid Design Studio - Registration Page
# =============================================================================
# Appears after the user taps a structure type on the Studio page.
#
# Contains:
#   - Project meta inputs (name, client, location, reference, engineer, date)
#   - Variant selection for the chosen structure type
#
# Design (agreed 2026-09-12 / 2026-09-13):
#   - Breadcrumb at top: "SDSe Fluid Design Studio / Structure Type"
#   - Project meta section
#   - Variant list for the selected structure type
#   - Tapping a variant advances to Workshop
#   - Back button returns to Studio
#
# Variants are defined in data/structures.py (VARIANTS dict) later.
# For now, this file holds the fallback variant catalogue.
#
# See PROJECT_STATE.md Section 20 for the variant mapping rules.
# =============================================================================

import streamlit as st

from data.structures import STRUCTURE_TYPES


# =============================================================================
# VARIANT CATALOGUE (FALLBACK)
# =============================================================================

VARIANTS_FALLBACK = {
    "saddle_span": [
        {
            "key": "standard_saddle",
            "name": "Standard Saddle",
            "description": "Two curved edge beams converging to two ground support points. Classic hypar form.",
            "available": True,
        },
        {
            "key": "frame_supported_saddle",
            "name": "Frame Supported Saddle",
            "description": "Standard saddle with additional rigid frame underneath for larger spans.",
            "available": True,
        },
        {
            "key": "cantilever_leaf",
            "name": "Cantilever Leaf",
            "description": "Uni-pole column with curved spine and radial ribs. Leaf-shaped membrane. Cantilevered.",
            "available": True,
        },
        {
            "key": "cantilever_flower",
            "name": "Cantilever Flower",
            "description": "Multi-leaf layered spiral. Future vision.",
            "available": False,
        },
    ],
    "tensile_sails": [
        {
            "key": "hypar_sail_3",
            "name": "Hypar Sail - 3 Anchors",
            "description": "Triangular hypar. Three anchor points at user-defined positions and heights.",
            "available": True,
        },
        {
            "key": "hypar_sail_4",
            "name": "Hypar Sail - 4 Anchors",
            "description": "Classic quad hypar. Four anchor points at user-defined positions and heights. Two high, two low typically.",
            "available": True,
        },
        {
            "key": "ridge_sail",
            "name": "Ridge Sail",
            "description": "Two membranes meeting at a ridge cable. Six anchor points at different heights.",
            "available": True,
        },
        {
            "key": "multiple_sails",
            "name": "Multiple Sails",
            "description": "Array of hypar sails side by side. Anchors can be shared between adjacent sails.",
            "available": True,
        },
        {
            "key": "wall_sail",
            "name": "Wall Sail",
            "description": "Membrane anchored on two walls at different heights.",
            "available": True,
        },
        {
            "key": "column_sail",
            "name": "Column Sail",
            "description": "Membrane anchored to four columns at different heights. No edge beams.",
            "available": True,
        },
    ],
    "framed_tensile": [
        {
            "key": "simple_frame",
            "name": "Simple Frame + Fabric",
            "description": "Straight frame members with fabric on top. Column-free interior.",
            "available": True,
        },
        {
            "key": "arched_frame",
            "name": "Arched Frame + Fabric",
            "description": "Curved arch members with fabric on top.",
            "available": True,
        },
        {
            "key": "trussed_frame",
            "name": "Trussed Frame + Fabric",
            "description": "Triangulated truss frame with fabric on top. Larger spans.",
            "available": True,
        },
    ],
    "unipole_tensile": [
        {
            "key": "single_cone",
            "name": "Single Cone",
            "description": "Radial symmetry. One mast with cone fabric and ring cable.",
            "available": True,
        },
        {
            "key": "multi_cone_cluster",
            "name": "Multi-Cone Cluster",
            "description": "Multiple cone units in a cluster.",
            "available": True,
        },
        {
            "key": "umbrella",
            "name": "Umbrella",
            "description": "Single mast with radial ribs and fabric. Umbrella form.",
            "available": True,
        },
    ],
    "canopy": [
        {
            "key": "cantilever_flat",
            "name": "Cantilever Flat Shade",
            "description": "Uni-pole with straight arm and flat shade surface.",
            "available": True,
        },
        {
            "key": "cantilever_bell",
            "name": "Cantilever Bell Shade",
            "description": "Uni-pole with curved arm and bell-shaped shade surface.",
            "available": True,
        },
        {
            "key": "cantilever_pyramid",
            "name": "Cantilever Pyramid Shade",
            "description": "Uni-pole with straight arm and pyramid shade surface.",
            "available": True,
        },
        {
            "key": "cantilever_cone",
            "name": "Cantilever Cone Shade",
            "description": "Uni-pole with cone fabric draped from top.",
            "available": True,
        },
        {
            "key": "cable_supported",
            "name": "Cable-Supported Cantilever",
            "description": "Mast with cables and shade surface.",
            "available": True,
        },
        {
            "key": "wall_mounted",
            "name": "Wall-Mounted Shade",
            "description": "Attached to a wall and cantilevered out.",
            "available": True,
        },
        {
            "key": "tree_canopy",
            "name": "Tree Canopy",
            "description": "Trunk with branching arms and shade. Future vision.",
            "available": False,
        },
    ],
    "frame_tent": [
        {
            "key": "pyramid_tent",
            "name": "Pyramid Tent",
            "description": "Four-sided pyramid. Central pole. Classic event tent.",
            "available": True,
        },
        {
            "key": "gable_tent",
            "name": "Gable Tent",
            "description": "Rectangular plan with a ridge line. Gable ends.",
            "available": True,
        },
        {
            "key": "hip_tent",
            "name": "Hip Tent",
            "description": "Four-sided with a short ridge. Hip ends.",
            "available": True,
        },
        {
            "key": "sail_tent",
            "name": "Sail Tent",
            "description": "Asymmetric sail-like tent. Free-form.",
            "available": True,
        },
    ],
    "portal_frame": [
        {
            "key": "simple_portal",
            "name": "Simple Portal",
            "description": "Single span. Two columns and one rafter.",
            "available": True,
        },
        {
            "key": "portal_with_mezzanine",
            "name": "With Mezzanine",
            "description": "Portal with an intermediate mezzanine floor.",
            "available": True,
        },
        {
            "key": "portal_with_crane",
            "name": "With Crane",
            "description": "Portal with crane gantry beams.",
            "available": True,
        },
        {
            "key": "multi_bay_portal",
            "name": "Multi-Bay Portal",
            "description": "Portal frame with multiple bays side by side.",
            "available": True,
        },
    ],
}


# =============================================================================
# CSS SPECIFIC TO REGISTRATION PAGE
# =============================================================================

REGISTRATION_CSS = """
    <style>
    .reg-breadcrumb {
        font-size: 0.85rem;
        color: #a8b8c8;
        margin-bottom: 1.2rem;
        letter-spacing: 0.3px;
    }
    .reg-breadcrumb .crumb {
        color: #f39c12;
        font-weight: 600;
    }

    .reg-section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #ffffff;
        margin: 1.4rem 0 0.8rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #1e2a3a;
    }

    .reg-variant-tile {
        background-color: #121e2e;
        border: 1px solid #1e2a3a;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        transition: all 0.25s ease;
    }
    .reg-variant-tile:hover {
        border-color: #f39c12;
    }
    .reg-variant-tile.disabled {
        opacity: 0.45;
    }
    .reg-variant-name {
        font-size: 1rem;
        font-weight: 600;
        color: #ffffff;
        margin: 0 0 0.3rem 0;
    }
    .reg-variant-desc {
        font-size: 0.85rem;
        color: #a8b8c8;
        margin: 0;
        line-height: 1.4;
    }
    .reg-variant-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-left: 6px;
        background-color: #f39c1233;
        color: #f39c12;
        border: 1px solid #f39c12;
    }
    </style>
"""


# =============================================================================
# HELPERS
# =============================================================================

def _get_variants(structure_key):
    """Return variant list for a structure type. Prefer data, fall back."""
    try:
        from data.structures import VARIANTS
        if VARIANTS and structure_key in VARIANTS:
            return VARIANTS[structure_key]
    except (ImportError, AttributeError):
        pass

    return VARIANTS_FALLBACK.get(structure_key, [])


def _initial_project_info():
    """Return default project meta if none exists."""
    if "project_info" not in st.session_state:
        st.session_state.project_info = {
            "name": "",
            "client": "",
            "location": "",
            "reference": "",
            "engineer": "",
            "date": "",
        }
    return st.session_state.project_info


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_registration():
    """
    Render the Registration page.
    Called by the navigation router when the app state is 'registration'.
    """
    st.markdown(REGISTRATION_CSS, unsafe_allow_html=True)

    structure_key = st.session_state.get("structure_key", "saddle_span")
    structure_name = st.session_state.get("structure_name", "Saddle Span")

    # ---- Breadcrumb
    st.markdown(
        '<div class="reg-breadcrumb">'
        'SDSe Fluid Design Studio / '
        '<span class="crumb">' + structure_name + '</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Project Information section
    st.markdown(
        '<div class="reg-section-header">Project Information</div>',
        unsafe_allow_html=True,
    )

    info = _initial_project_info()

    col1, col2 = st.columns(2)
    with col1:
        info["name"] = st.text_input(
            "Project Name",
            value=info.get("name", ""),
            placeholder="e.g., OCB Entrance Canopy",
            key="reg_project_name",
        )
        info["client"] = st.text_input(
            "Client Name",
            value=info.get("client", ""),
            placeholder="e.g., OCBC Bank",
            key="reg_client_name",
        )
        info["location"] = st.text_input(
            "Location",
            value=info.get("location", ""),
            placeholder="e.g., Kuala Lumpur",
            key="reg_location",
        )

    with col2:
        info["reference"] = st.text_input(
            "Project Reference",
            value=info.get("reference", ""),
            placeholder="e.g., SDSe-2026-001",
            key="reg_reference",
        )
        info["engineer"] = st.text_input(
            "Engineer",
            value=info.get("engineer", ""),
            placeholder="Your name",
            key="reg_engineer",
        )
        info["date"] = st.text_input(
            "Date",
            value=info.get("date", ""),
            placeholder="YYYY-MM-DD",
            key="reg_date",
        )

    st.session_state.project_info = info

    # ---- Variant selection
    st.markdown(
        '<div class="reg-section-header">Choose a Variant</div>',
        unsafe_allow_html=True,
    )

    variants = _get_variants(structure_key)

    if not variants:
        st.info("Variants for this structure type are coming soon.")
        return

    for variant in variants:
        vkey = variant.get("key", "")
        vname = variant.get("name", "")
        vdesc = variant.get("description", "")
        vavail = variant.get("available", True)

        badge_html = ""
        if not vavail:
            badge_html = '<span class="reg-variant-badge">Coming Soon</span>'

        cls = "reg-variant-tile"
        if not vavail:
            cls += " disabled"

        tile_html = (
            '<div class="' + cls + '">'
            '<div class="reg-variant-name">' + vname + badge_html + '</div>'
            '<div class="reg-variant-desc">' + vdesc + '</div>'
            '</div>'
        )
        st.markdown(tile_html, unsafe_allow_html=True)

        if vavail:
            if st.button(
                "Select " + vname,
                key="reg_variant_" + structure_key + "_" + vkey,
                use_container_width=True,
            ):
                st.session_state.variant_key = vkey
                st.session_state.variant_name = vname
                st.session_state.page = "workshop"
                st.rerun()
        else:
            st.button(
                "Coming Soon",
                key="reg_variant_" + structure_key + "_" + vkey,
                use_container_width=True,
                disabled=True,
            )

        st.markdown('<div style="height: 0.2rem;"></div>', unsafe_allow_html=True)

    # ---- Back button
    st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
    if st.button("Back to Studio", key="reg_back_studio", use_container_width=True):
        st.session_state.page = "studio"
        st.rerun()
