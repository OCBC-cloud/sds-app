# =============================================================================
# SDSe Fluid Design Studio - Registration Page
# =============================================================================
# Project meta inputs + variant selection.
# Date is captured automatically on first visit and never overwritten.
# =============================================================================

from datetime import datetime

import streamlit as st


VARIANTS_FALLBACK = {
    "saddle_span": [
        {"key": "standard_saddle", "name": "Standard Saddle",
         "description": "Two curved edge beams converging to two ground support points. Classic hypar form.",
         "available": True},
        {"key": "frame_supported_saddle", "name": "Frame Supported Saddle",
         "description": "Standard saddle with additional rigid frame underneath for larger spans.",
         "available": True},
        {"key": "cantilever_leaf", "name": "Cantilever Leaf",
         "description": "Uni-pole column with curved spine and radial ribs. Leaf-shaped membrane. Cantilevered.",
         "available": True},
        {"key": "cantilever_flower", "name": "Cantilever Flower",
         "description": "Multi-leaf layered spiral. Future vision.",
         "available": False},
    ],
    "tensile_true_sails": [
        {"key": "hypar_sail_3", "name": "Hypar Sail - 3 Anchors",
         "description": "Triangular hypar. Three anchor points at user-defined positions and heights.",
         "available": True},
        {"key": "hypar_sail_4", "name": "Hypar Sail - 4 Anchors",
         "description": "Classic quad hypar. Four anchor points at user-defined positions and heights.",
         "available": True},
        {"key": "ridge_sail", "name": "Ridge Sail",
         "description": "Two membranes meeting at a ridge cable. Six anchor points.",
         "available": True},
        {"key": "multiple_sails", "name": "Multiple Sails",
         "description": "Array of hypar sails side by side.",
         "available": True},
        {"key": "wall_sail", "name": "Wall Sail",
         "description": "Membrane anchored on two walls at different heights.",
         "available": True},
        {"key": "column_sail", "name": "Column Sail",
         "description": "Membrane anchored to four columns at different heights.",
         "available": True},
    ],
    "framed_tensile": [
        {"key": "simple_frame", "name": "Simple Frame + Fabric",
         "description": "Straight frame members with fabric on top.",
         "available": True},
        {"key": "arched_frame", "name": "Arched Frame + Fabric",
         "description": "Curved arch members with fabric on top.",
         "available": True},
        {"key": "trussed_frame", "name": "Trussed Frame + Fabric",
         "description": "Triangulated truss frame with fabric on top. Larger spans.",
         "available": True},
    ],
    "unipole_tensile": [
        {"key": "single_cone", "name": "Single Cone",
         "description": "Radial symmetry. One mast with cone fabric and ring cable.",
         "available": True},
        {"key": "multi_cone_cluster", "name": "Multi-Cone Cluster",
         "description": "Multiple cone units in a cluster.",
         "available": True},
        {"key": "umbrella", "name": "Umbrella",
         "description": "Single mast with radial ribs and fabric. Umbrella form.",
         "available": True},
    ],
    "canopy": [
        {"key": "cantilever_flat", "name": "Cantilever Flat Shade",
         "description": "Uni-pole with straight arm and flat shade surface.",
         "available": True},
        {"key": "cantilever_bell", "name": "Cantilever Bell Shade",
         "description": "Uni-pole with curved arm and bell-shaped shade surface.",
         "available": True},
        {"key": "cantilever_pyramid", "name": "Cantilever Pyramid Shade",
         "description": "Uni-pole with straight arm and pyramid shade surface.",
         "available": True},
        {"key": "cantilever_cone", "name": "Cantilever Cone Shade",
         "description": "Uni-pole with cone fabric draped from top.",
         "available": True},
        {"key": "cable_supported", "name": "Cable-Supported Cantilever",
         "description": "Mast with cables and shade surface.",
         "available": True},
        {"key": "wall_mounted", "name": "Wall Mounted Shade",
         "description": "Attached to a wall and cantilevered out.",
         "available": True},
        {"key": "tree_canopy", "name": "Tree Canopy",
         "description": "Trunk with branching arms and shade. Future vision.",
         "available": False},
    ],
    "frame_tent": [
        {"key": "pyramid_tent", "name": "Pyramid Tent",
         "description": "Four-sided pyramid. Central pole. Classic event tent.",
         "available": True},
        {"key": "gable_tent", "name": "Gable Tent",
         "description": "Rectangular plan with a ridge line. Gable ends.",
         "available": True},
        {"key": "hip_tent", "name": "Hip Tent",
         "description": "Four-sided with a short ridge. Hip ends.",
         "available": True},
        {"key": "sail_tent", "name": "Sail Tent",
         "description": "Asymmetric sail-like tent. Free-form.",
         "available": True},
    ],
    "portal_frame": [
        {"key": "simple_portal", "name": "Simple Portal",
         "description": "Single span. Two columns and one rafter.",
         "available": True},
        {"key": "portal_with_mezzanine", "name": "With Mezzanine",
         "description": "Portal with an intermediate mezzanine floor.",
         "available": True},
        {"key": "portal_with_crane", "name": "With Crane",
         "description": "Portal with crane gantry beams.",
         "available": True},
        {"key": "multi_bay_portal", "name": "Multi-Bay Portal",
         "description": "Portal frame with multiple bays side by side.",
         "available": True},
    ],
}


def _get_variants(structure_key):
    return VARIANTS_FALLBACK.get(structure_key, [])


def render_registration():
    structure_key = st.session_state.get("structure_key", "saddle_span")
    structure_name = st.session_state.get("structure_name", "Saddle Span")

    if "project_info" not in st.session_state:
        st.session_state.project_info = {
            "name": "",
            "client": "",
            "location": "",
            "reference": "",
            "engineer": "",
            "date": "",
        }

    info = st.session_state.project_info

    # Auto-capture date/time on first visit and never overwrite.
    if not info.get("date"):
        info["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    st.markdown(
        '<div style="font-size: 0.85rem; color: #a8b8c8; margin-bottom: 1.2rem;">'
        'SDSe Fluid Design Studio / '
        '<span style="color: #f39c12; font-weight: 600;">' + structure_name + '</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700; '
        'margin: 0 0 0.6rem 0; padding-bottom: 0.4rem; '
        'border-bottom: 1px solid #1e2a3a;">Project Information</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        info["name"] = st.text_input("Project Name", value=info.get("name", ""), key="reg_pname")
        info["client"] = st.text_input("Client Name", value=info.get("client", ""), key="reg_cname")
        info["location"] = st.text_input("Location", value=info.get("location", ""), key="reg_loc")
    with col2:
        info["reference"] = st.text_input("Project Reference", value=info.get("reference", ""), key="reg_ref")
        info["engineer"] = st.text_input("Engineer", value=info.get("engineer", ""), key="reg_eng")
        st.caption("Created: " + info["date"])

    st.session_state.project_info = info

    st.markdown(
        '<div style="color: #ffffff; font-size: 1.15rem; font-weight: 700; '
        'margin: 1.4rem 0 0.6rem 0; padding-bottom: 0.4rem; '
        'border-bottom: 1px solid #1e2a3a;">Choose a Variant</div>',
        unsafe_allow_html=True,
    )

    variants = _get_variants(structure_key)

    if not variants:
        st.info("Variants for this structure type are coming soon.")
        return

    for variant in variants:
        vk = variant.get("key", "")
        vn = variant.get("name", "")
        vd = variant.get("description", "")
        va = variant.get("available", True)

        badge = ""
        if not va:
            badge = ('<span style="display: inline-block; padding: 2px 8px; '
                     'border-radius: 10px; font-size: 0.7rem; font-weight: 600; '
                     'background: #f39c1233; color: #f39c12; '
                     'border: 1px solid #f39c12; margin-left: 6px;">Coming Soon</span>')

        st.markdown(
            '<div style="background: #121e2e; border: 1px solid #1e2a3a; '
            'border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.6rem;">'
            '<div style="color: #ffffff; font-size: 1rem; font-weight: 600; '
            'margin-bottom: 0.3rem;">' + vn + badge + '</div>'
            '<div style="color: #a8b8c8; font-size: 0.85rem; line-height: 1.4;">'
            + vd + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        if va:
            if st.button("Select " + vn, key="reg_var_" + structure_key + "_" + vk, use_container_width=True):
                st.session_state.variant_key = vk
                st.session_state.variant_name = vn
                st.session_state.page = "workshop"
                st.rerun()
        else:
            st.button("Coming Soon", key="reg_var_na_" + structure_key + "_" + vk,
                      use_container_width=True, disabled=True)

    st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
    if st.button("Back to Studio", key="reg_back", use_container_width=True):
        st.session_state.page = "studio"
        st.rerun()
